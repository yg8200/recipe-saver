import io
from PIL import Image, ImageOps, UnidentifiedImageError
import pillow_heif

# Register HEIF opener so Pillow can open .heic files
pillow_heif.register_heif_opener()

def process_and_compress_image(image_bytes: bytes, max_size: int = 1500) -> bytes:
    """Turns any supported image into a JPEG no larger than max_size on its longest side."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The uploaded file is not a valid or supported image.") from exc

    # Apply the EXIF orientation so phone photos are not sent sideways to the OCR model
    image = ImageOps.exif_transpose(image)

    # JPEG can't store transparency (RGBA PNGs)
    if image.mode != "RGB":
        image = image.convert("RGB")

    if image.width > max_size or image.height > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=85, optimize=True)
    
    return output_buffer.getvalue()