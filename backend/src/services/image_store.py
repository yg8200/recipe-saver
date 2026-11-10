"""Saving and deleting dish photos on disk."""
import os
import uuid

from flask import current_app

from src.utils.image_processing import process_and_compress_image

# Dish photos are shown at most ~1100px wide, so 1200px is plenty and keeps files small.
MAX_DISH_IMAGE_SIZE = 1200


def upload_dir() -> str:
    path = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(path, exist_ok=True)
    return path


def save_recipe_image(image_bytes: bytes) -> str:
    """Validates, resizes and re-encodes the image as JPEG, then stores it. Returns the file name.

    Raises ValueError if the bytes are not a real image. Re-encoding also strips metadata such as
    GPS location from phone photos, and means we never serve the uploaded bytes as they came in.
    """
    jpeg_bytes = process_and_compress_image(image_bytes, max_size=MAX_DISH_IMAGE_SIZE)
    # A random name avoids clashes and means one recipe's photo URL can't be guessed from another's
    filename = f"{uuid.uuid4().hex}.jpg"
    with open(os.path.join(upload_dir(), filename), "wb") as f:
        f.write(jpeg_bytes)
    return filename


def delete_recipe_image(filename: str | None) -> None:
    """Removes a stored photo. Missing files and odd names are ignored."""
    # basename check: never let a stored value walk out of the upload folder
    if not filename or os.path.basename(filename) != filename:
        return
    try:
        os.remove(os.path.join(upload_dir(), filename))
    except FileNotFoundError:
        pass
