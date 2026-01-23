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
    model_name: str = "Tongyi-MAI/Z-Image-Turbo", subfolder: str = "scheduler"
):
    """
    Load a scheduler from a pretrained model repository.

    Args:
         model_name: The name or path of the pretrained model.
        subfolder: The name of the scheduler subfolder in the Hugging Face model repository.
    """
    return FlowMatchEulerDiscreteScheduler.from_pretrained(
        model_name, subfolder=subfolder
    )


def load_diffusion_transformer(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "transformer",
    device: str = "cuda:0",
) -> AnnotatedDict[Literal["dit_model", "dit_hook"]]:
    """
    Load a diffusion transformer from a pretrained model repository.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the diffusion transformer subfolder in the Hugging Face model repository.
        device: The execution device for the model

    Returns:
        A dictionary with 2 keys: 'dit_model' and 'dit_hook'
    """
    diffusers_logging.set_verbosity_info()
    model = ZImageTransformer2DModel.from_pretrained(
        model_name,
        subfolder=subfolder,
        torch_dtype=torch.bfloat16,
    )
    model, hook = cpu_offload_with_hook(model, execution_device=device)
    return {"dit_model": model, "dit_hook": hook}


def load_vae(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "vae",
    vae_scale_factor: int | None = None,
    device: str = "cuda:0",
) -> AnnotatedDict[Literal["vae_model", "vae_hook", "vae_image_processor"]]:
    """
    Load a VAE from a pretrained model repository.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the VAE subfolder in the Hugging Face model repository.
        device: The execution device for the model

    Returns:
        A dictionary with 3 keys: 'vae_model', 'vae_hook', and 'vae_image_processor'
    """
    diffusers_logging.set_verbosity_info()
    model = AutoencoderKL.from_pretrained(
        model_name,
        subfolder=subfolder,
        torch_dtype=torch.bfloat16,
    )
    model, hook = cpu_offload_with_hook(model, execution_device=device)
    vae_scale_factor = (
        2 ** (len(model.config.block_out_channels) - 1)
        if vae_scale_factor is None
        else vae_scale_factor
    )
    image_processor = VaeImageProcessor(vae_scale_factor=vae_scale_factor * 2)
    return {
        "vae_model": model,
        "vae_hook": hook,
        "vae_image_processor": image_processor,
    }


# ============================== Encode Prompts ============================== #


def encode_prompt(
    prompt: str,
    tokenizer: PreTrainedTokenizerBase,
    text_encoder: Qwen3Model,
    text_encoder_hook: UserCpuOffloadHook,
    max_sequence_length: int = 512,
    device: str = "cuda:0",
) -> list[torch.Tensor]:
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
    embeddngs_list = [
        prompt_embeddings[i][prompt_masks[i]] for i in range(len(prompt_embeddings))
    ]
    return embeddngs_list
