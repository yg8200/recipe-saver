import io
from PIL import Image, ImageOps, UnidentifiedImageError
import pillow_heif

# Register HEIF opener so Pillow can open .heic files
pillow_heif.register_heif_opener()

def process_and_compress_image(image_bytes: bytes, max_size: int = 1500) -> bytes:
    """
    Reads image bytes, converts to RGB (handling HEIC/PNG formats),
    resizes it to a maximum dimension while maintaining aspect ratio,
    and returns optimized JPEG bytes.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The uploaded file is not a valid or supported image.") from exc

    # Apply the EXIF orientation so phone photos are not sent sideways to the OCR model
    image = ImageOps.exif_transpose(image)

    # Convert to standard RGB (required for saving as JPEG)
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize only if the image is larger than our max_size limit
    if image.width > max_size or image.height > max_size:
        # thumbnail modifies the image in-place and preserves aspect ratio
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Save to buffer with optimization and 85% quality to save bandwidth/time
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=85, optimize=True)
    
    return output_buffer.getvalue()