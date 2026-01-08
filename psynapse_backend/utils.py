import base64
from io import BytesIO

from PIL import Image


def pil_image_to_openai_string(image: Image.Image, format: str = "PNG") -> str:
    """Convert a PIL Image to a base64-encoded string in the format "data:image/png;base64,..."

    Args:
        image: PIL Image object
        format: Image format (default: "PNG")

    Returns:
        Base64 encoded image string
    """
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    mime_type = f"image/{format.lower()}"
    return f"data:{mime_type};base64,{img_base64}"


def openai_string_to_pil_image(image_str: str) -> Image.Image:
    """Convert a base64-encoded image string back to PIL Image.

    Args:
        image_str: Base64 encoded image string in format "data:image/png;base64,..."

    Returns:
        PIL Image object
    """
    # Remove the data URL prefix if present
    if image_str.startswith("data:"):
        image_str = image_str.split(",", 1)[1]

    img_bytes = base64.b64decode(image_str)
    return Image.open(BytesIO(img_bytes))
