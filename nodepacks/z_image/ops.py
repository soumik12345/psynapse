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

# ============================== Load Diffusion Pipeline Components ============================== #


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
    num_inference_steps: int = 50,
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


# ============================== Encode Prompts ============================== #


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
) -> torch.Tensor:
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
    return randn_tensor(shape, device=device, dtype=torch.bfloat16)


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


# if __name__ == "__main__":
#     tokenizer = load_tokenizer()

#     text_encoder_result = load_text_encoder()
#     text_encoder = text_encoder_result["text_encoder_model"]
#     text_encoder_hook = text_encoder_result["text_encoder_hook"]

#     prompt = "A fantasy landscape with mountains and a river, detailed, vibrant colors"
#     embeddings = encode_prompt(
#         prompt,
#         tokenizer,
#         text_encoder,
#         text_encoder_hook,
#     )

#     vae_result = load_vae()
#     vae = vae_result["vae_model"]
#     vae_hook = vae_result["vae_hook"]
#     vae_scale_factor = vae_result["vae_scale_factor"]
#     vae_image_processor = vae_result["vae_image_processor"]

#     dit_result = load_diffusion_transformer()
#     dit = dit_result["dit_model"]
#     dit_hook = dit_result["dit_hook"]

#     latents = initialize_random_latents(
#         height=1024,
#         width=1024,
#         num_channels_latents=dit.in_channels,
#         vae_scale_factor=vae_scale_factor,
#         device="cuda:0",
#     )

#     image_seq_len = (latents.shape[2] // 2) * (latents.shape[3] // 2)
#     timestep_shift = calculate_timestep_shift(image_seq_len=image_seq_len)
#     scheduler_results = load_scheduler(timestep_shift=timestep_shift)
#     timesteps = scheduler_results["timesteps"]
#     num_warmup_steps = scheduler_results["num_warmup_steps"]
