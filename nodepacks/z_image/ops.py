from typing import Literal

import torch
from transformers import AutoTokenizer, PreTrainedTokenizerBase
from transformers.models.qwen3.modeling_qwen3 import Qwen3Model
from transformers.utils import logging as transformers_logging

from psynapse_backend.schema_extractor import AnnotatedDict


def load_tokenizer(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo", subfolder: str = "tokenizer"
) -> PreTrainedTokenizerBase:
    """Load a tokenizer from a pretrained model.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the subfolder in the Hugging Face model repository.

    Returns:
        A tokenizer instance.
    """
    return AutoTokenizer.from_pretrained(model_name, subfolder=subfolder)


def load_text_encoder(
    model_name: str = "Tongyi-MAI/Z-Image-Turbo",
    subfolder: str = "text_encoder",
    device_map: str = "cuda:0",
) -> AnnotatedDict[Literal["text_encoder_model", "text_encoder_hook"]]:
    """Load a text encoder from a pretrained model.

    Args:
        model_name: The name or path of the pretrained model.
        subfolder: The name of the subfolder in the Hugging Face model repository.
        device_map:

    Returns:
        A dictionary with 2 keys: 'text_encoder_model' and 'text_encoder_hook'
    """
    transformers_logging.set_verbosity_info()
    model = Qwen3Model.from_pretrained(
        model_name,
        subfolder=subfolder,
        dtype=torch.bfloat16,
    ).to(device_map)
    # TODO: Add CPU offloading
    return {"text_encoder_model": model, "text_encoder_hook": None}
