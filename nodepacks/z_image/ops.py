from transformers import AutoTokenizer, PreTrainedTokenizerBase


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
