from typing import Literal

import torch
from accelerate import cpu_offload_with_hook
from accelerate.hooks import UserCpuOffloadHook
from diffusers import (
    AutoencoderKL,
    FlowMatchEulerDiscreteScheduler,
    ZImageTransformer2DModel,
    logging as diffusers_logging,
)
from diffusers.image_processor import VaeImageProcessor
from diffusers.utils.torch_utils import randn_tensor
from transformers import AutoTokenizer, PreTrainedTokenizerBase
from transformers.models.qwen3.modeling_qwen3 import Qwen3Model
from transformers.utils import logging as transformers_logging

from psynapse_backend.schema_extractor import AnnotatedDict
from psynapse_backend.stateful_op_utils import ProgressReporter


def load_tokenizer(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo", subfolder: str = "tokenizer"
) -> PreTrainedTokenizerBase:
    """Load a tokenizer from a pretrained model.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the tokenizer subfolder in the Hugging Face model repository.

    Returns:
        A tokenizer instance.
    """
    return AutoTokenizer.from_pretrained(model_name, subfolder=subfolder)


def load_text_encoder(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "text_encoder",
    device: str = "cuda:0",
) -> AnnotatedDict[Literal["text_encoder_model", "text_encoder_hook"]]:
    """Load a text encoder from a pretrained model.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the text encoder subfolder in the Hugging Face model repository.
        device: The execution device for the model

    Returns:
        A dictionary with 2 keys: 'text_encoder_model' and 'text_encoder_hook'
    """
    transformers_logging.set_verbosity_info()
    model = Qwen3Model.from_pretrained(
        model_name,
        subfolder=subfolder,
        dtype=torch.bfloat16,
    )
    model, hook = cpu_offload_with_hook(model, execution_device=device)
    return {"text_encoder_model": model, "text_encoder_hook": hook}


def load_scheduler(
    timestep_shift: float,
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "scheduler",
    num_inference_steps: int = 9,
    device: str = "cuda:0",
) -> AnnotatedDict[Literal["scheduler", "timesteps", "num_warmup_steps"]]:
    """
    Load a scheduler from a pretrained model repository.

    Args:
         model_name: The name or path of the pretrained model.
        subfolder: The name of the scheduler subfolder in the Hugging Face model repository.
        num_inference_steps: The number of inference steps to use for the scheduler.
        device: The execution device for the scheduler.

    Returns:
        A dictionary with 3 keys: 'scheduler', 'timesteps', and 'num_warmup_steps'
    """
    scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(
        model_name, subfolder=subfolder
    )
    scheduler.sigma_min = 0.0
    scheduler.set_timesteps(num_inference_steps, device=device, mu=timestep_shift)
    timesteps = scheduler.timesteps
    num_warmup_steps = max(len(timesteps) - num_inference_steps * scheduler.order, 0)
    return {
        "scheduler": scheduler,
        "timesteps": timesteps,
        "num_warmup_steps": num_warmup_steps,
    }


def load_diffusion_transformer(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "transformer",
    device: str = "cuda:0",
) -> AnnotatedDict[Literal["dit_model", "dit_hook", "num_channels_latents"]]:
    """
    Load a diffusion transformer from a pretrained model repository.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the diffusion transformer subfolder in the Hugging Face model repository.
        device: The execution device for the model

    Returns:
        A dictionary with 3 keys: 'dit_model', 'dit_hook', and 'num_channels_latents'
    """
    diffusers_logging.set_verbosity_info()
    model = ZImageTransformer2DModel.from_pretrained(
        model_name,
        subfolder=subfolder,
        torch_dtype=torch.bfloat16,
    )
    model, hook = cpu_offload_with_hook(model, execution_device=device)
    return {
        "dit_model": model,
        "dit_hook": hook,
        "num_channels_latents": model.in_channels,
    }


def load_vae(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "vae",
    device: str = "cuda:0",
) -> AnnotatedDict[
    Literal["vae_model", "vae_hook", "vae_scale_factor", "vae_image_processor"]
]:
    """
    Load a VAE from a pretrained model repository.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the VAE subfolder in the Hugging Face model repository.
        device: The execution device for the model

    Returns:
        A dictionary with 4 keys: 'vae_model', 'vae_hook', 'vae_scale_factor', and 'vae_image_processor'
    """
    diffusers_logging.set_verbosity_info()
    model = AutoencoderKL.from_pretrained(
        model_name,
        subfolder=subfolder,
        torch_dtype=torch.bfloat16,
    )
    model, hook = cpu_offload_with_hook(model, execution_device=device)
    vae_scale_factor = 2 ** (len(model.config.block_out_channels) - 1)
    image_processor = VaeImageProcessor(vae_scale_factor=vae_scale_factor * 2)
    return {
        "vae_model": model,
        "vae_hook": hook,
        "vae_scale_factor": vae_scale_factor,
        "vae_image_processor": image_processor,
    }


@torch.no_grad()
def encode_prompt(
    prompt: str,
    tokenizer: PreTrainedTokenizerBase,
    text_encoder: Qwen3Model,
    text_encoder_hook: UserCpuOffloadHook,
    max_sequence_length: int = 512,
    device: str = "cuda:0",
) -> list[torch.Tensor]:
    """
    Encodes a prompt into a list of embeddings.

    Args:
        prompt: The prompt to encode.
        tokenizer: The tokenizer to use for encoding.
        text_encoder: The text encoder to use for encoding.
        text_encoder_hook: The hook to use for offloading the text encoder.
        max_sequence_length: The maximum sequence length for the tokenizer.
        device: The device to run the model on.

    Returns:
        A list of embeddings.
    """
    prompt = [prompt]
    for i, prompt_item in enumerate(prompt):
        messages = [{"role": "user", "content": prompt_item}]
        prompt_item = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True,
        )
        prompt[i] = prompt_item
    text_inputs = tokenizer(
        prompt,
        padding="max_length",
        max_length=max_sequence_length,
        truncation=True,
        return_tensors="pt",
    )
    text_input_ids = text_inputs.input_ids.to(device)
    prompt_masks = text_inputs.attention_mask.to(device).bool()
    prompt_embeddings = text_encoder(
        input_ids=text_input_ids,
        attention_mask=prompt_masks,
        output_hidden_states=True,
    ).hidden_states[-2]
    embeddings_list = [
        prompt_embeddings[i][prompt_masks[i]] for i in range(len(prompt_embeddings))
    ]
    text_encoder_hook.offload()
    return embeddings_list


@torch.no_grad()
def initialize_random_latents(
    height: int,
    width: int,
    vae_scale_factor: int,
    num_channels_latents: int,
    device: str = "cuda:0",
) -> AnnotatedDict[Literal["latents", "image_seq_len"]]:
    """
    Creates random noise tensors sampled from a Gaussian distribution that will be iteratively denoised into a coherent image,

    Args:
        height: The height of the image.
        width: The width of the image.
        vae_scale_factor: The scale factor of the VAE.
        device: The device to run the model on.

    Returns:
        A random noise tensor sampled from a Gaussian distribution.
    """
    height = 2 * (int(height) // (vae_scale_factor * 2))
    width = 2 * (int(width) // (vae_scale_factor * 2))
    shape = (1, num_channels_latents, height, width)
    latents = randn_tensor(shape, device=device, dtype=torch.bfloat16)
    image_seq_len = (latents.shape[2] // 2) * (latents.shape[3] // 2)
    return {
        "latents": latents,
        "image_seq_len": image_seq_len,
    }


def calculate_timestep_shift(
    image_seq_len,
    base_seq_len: int = 256,
    max_seq_len: int = 4096,
    base_shift: float = 0.5,
    max_shift: float = 1.15,
) -> float:
    """
    Calculate the resolution-dependent timestep shift parameter (`mu`) for flow-matching diffusion models like FLUX.
    It enables dynamic adjustment of the noise schedule based on image resolution.

    Args:
        image_seq_len: The length of the image sequence.
        base_seq_len: The base length of the image sequence.
        max_seq_len: The maximum length of the image sequence.
        base_shift: The base shift parameter.
        max_shift: The maximum shift parameter.

    Returns:
        The resolution-dependent timestep shift parameter.
    """
    slope = (max_shift - base_shift) / (max_seq_len - base_seq_len)
    y_intercept = base_shift - slope * base_seq_len
    timestep_shift = image_seq_len * slope + y_intercept
    return timestep_shift


class DenoisingDiffusion:
    def __init__(self):
        self._progress_reporter = ProgressReporter()

    @torch.no_grad()
    def __call__(
        self,
        prompt_embeddings: list[torch.Tensor],
        latents: torch.Tensor,
        scheduler: FlowMatchEulerDiscreteScheduler,
        timesteps: torch.Tensor,
        transformer: ZImageTransformer2DModel,
        transformer_hook: UserCpuOffloadHook,
        guidance_scale: float = 0.0,
        cfg_normalization: bool = False,
        cfg_truncation: float = 1.0,
        negative_prompt_embeddings: list[torch.Tensor] | None = None,
    ) -> AnnotatedDict[Literal["denoised_latents"]]:
        """
        The core denoising loop that iteratively removes noise from the latents.

        Args:
            prompt_embeddings: List of prompt embeddings.
            latents: The noisy latent tensor to denoise.
            scheduler: The scheduler to use for denoising.
            timesteps: The timesteps to use for denoising.
            transformer: The diffusion transformer model.
            transformer_hook: The hook to use for offloading the transformer.
            guidance_scale: Guidance scale for classifier-free guidance.
                Values > 1 enable CFG.
            cfg_normalization: Whether to apply CFG normalization.
            cfg_truncation: Truncation value for CFG (0-1). CFG is disabled
                for normalized time values > cfg_truncation.
            negative_prompt_embeddings: List of negative prompt embeddings
                (required if guidance_scale > 1).

        Returns:
            A dictionary with 'denoised_latents' key containing the denoised latent tensor.
        """
        do_classifier_free_guidance = guidance_scale > 1.0
        actual_batch_size = latents.shape[0]

        if do_classifier_free_guidance:
            if negative_prompt_embeddings is None:
                raise ValueError(
                    "negative_prompt_embeddings is required when guidance_scale > 1"
                )

        for i, t in enumerate(timesteps):
            # Expand timestep to batch dimension
            timestep = t.expand(latents.shape[0])
            # Normalize timestep to [0, 1] range
            timestep = (1000 - timestep) / 1000
            # Get normalized time for cfg truncation check
            t_norm = timestep[0].item()

            # Handle cfg truncation
            current_guidance_scale = guidance_scale
            if (
                do_classifier_free_guidance
                and cfg_truncation is not None
                and cfg_truncation <= 1
            ):
                if t_norm > cfg_truncation:
                    current_guidance_scale = 0.0

            # Run CFG only if configured AND scale is non-zero
            apply_cfg = do_classifier_free_guidance and current_guidance_scale > 0

            if apply_cfg:
                latents_typed = latents.to(transformer.dtype)
                latent_model_input = latents_typed.repeat(2, 1, 1, 1)
                prompt_embeds_model_input = (
                    prompt_embeddings + negative_prompt_embeddings
                )
                timestep_model_input = timestep.repeat(2)
            else:
                latent_model_input = latents.to(transformer.dtype)
                prompt_embeds_model_input = prompt_embeddings
                timestep_model_input = timestep

            # Add temporal dimension (for video compatibility in the model)
            latent_model_input = latent_model_input.unsqueeze(2)
            latent_model_input_list = list(latent_model_input.unbind(dim=0))

            # Forward pass through transformer
            model_out_list = transformer(
                latent_model_input_list,
                timestep_model_input,
                prompt_embeds_model_input,
                return_dict=False,
            )[0]

            if apply_cfg:
                # Perform CFG
                pos_out = model_out_list[:actual_batch_size]
                neg_out = model_out_list[actual_batch_size:]

                noise_pred = []
                for j in range(actual_batch_size):
                    pos = pos_out[j].float()
                    neg = neg_out[j].float()

                    pred = pos + current_guidance_scale * (pos - neg)

                    # Renormalization
                    if cfg_normalization and float(cfg_normalization) > 0.0:
                        ori_pos_norm = torch.linalg.vector_norm(pos)
                        new_pos_norm = torch.linalg.vector_norm(pred)
                        max_new_norm = ori_pos_norm * float(cfg_normalization)
                        if new_pos_norm > max_new_norm:
                            pred = pred * (max_new_norm / new_pos_norm)

                    noise_pred.append(pred)

                noise_pred = torch.stack(noise_pred, dim=0)
            else:
                noise_pred = torch.stack([out.float() for out in model_out_list], dim=0)

            # Remove temporal dimension
            noise_pred = noise_pred.squeeze(2)
            # Negate the noise prediction (model predicts velocity / negative noise)
            noise_pred = -noise_pred

            # Compute the previous noisy sample x_t -> x_t-1
            latents = scheduler.step(
                noise_pred.to(torch.float32), t, latents, return_dict=False
            )[0]

        transformer_hook.offload()
        return {"denoised_latents": latents}


@torch.no_grad()
def decode_latents(
    latents: torch.Tensor,
    vae: AutoencoderKL,
    vae_hook: UserCpuOffloadHook,
    image_processor: VaeImageProcessor,
) -> list:
    """
    Decode latents to PIL images using the VAE.

    Args:
        latents: The denoised latent tensor.
        vae: The VAE model for decoding.
        vae_hook: The hook for offloading the VAE.
        image_processor: The image processor for post-processing.

    Returns:
        A list of PIL images.
    """
    latents = latents.to(vae.dtype)
    # Apply scaling and shift factors from VAE config
    latents = (latents / vae.config.scaling_factor) + vae.config.shift_factor

    # Decode latents to image
    image = vae.decode(latents, return_dict=False)[0]

    # Post-process to PIL images
    images = image_processor.postprocess(image, output_type="pil")

    vae_hook.offload()
    return images
