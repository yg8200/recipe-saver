import io
import os
from unittest.mock import patch

from src.core.database import db

NEW = {"title": "Cake", "ingredients": ["flour"], "instructions": ["bake"]}


def _recipe(client):
    return client.post("/recipes", json=NEW).get_json()


def _upload(client, recipe_id, payload, name="dish.jpg"):
    return client.post(
        f"/recipes/{recipe_id}/image", data={"image": (io.BytesIO(payload), name)},
        content_type="multipart/form-data",
    )


def _files(app):
    folder = app.config["UPLOAD_FOLDER"]
    return os.listdir(folder) if os.path.isdir(folder) else []


# A recipe has no photo until one is added.
def test_new_recipe_has_no_image(client):
    assert _recipe(client)["image_url"] is None


# Uploading a photo stores it, links it to the recipe and returns its URL.
def test_upload_image_attaches_photo(client, app, jpeg_bytes):
    recipe = _recipe(client)
    response = _upload(client, recipe["id"], jpeg_bytes)

    assert response.status_code == 200
    image_url = response.get_json()["image_url"]
    assert image_url.startswith("/images/") and image_url.endswith(".jpg")
    assert len(_files(app)) == 1
    assert client.get(f"/recipes/{recipe['id']}").get_json()["image_url"] == image_url


# The stored photo is served as a cacheable JPEG.
def test_get_image_serves_the_file(client, jpeg_bytes):
    recipe = _recipe(client)
    image_url = _upload(client, recipe["id"], jpeg_bytes).get_json()["image_url"]

    response = client.get(image_url)

    assert response.status_code == 200
    assert response.mimetype == "image/jpeg"
    assert "max-age=31536000" in response.headers["Cache-Control"]


# Replacing a photo deletes the old file so storage doesn't fill with orphans.
def test_replacing_image_deletes_the_old_file(client, app, jpeg_bytes):
    recipe = _recipe(client)
    first = _upload(client, recipe["id"], jpeg_bytes).get_json()["image_url"]
    second = _upload(client, recipe["id"], jpeg_bytes).get_json()["image_url"]

    assert first != second
    assert _files(app) == [second.split("/")[-1]]


# A big photo is shrunk to at most 1200px and re-encoded as JPEG.
def test_large_image_is_resized(client, app):
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (3000, 2000), "white").save(buffer, format="PNG")
    recipe = _recipe(client)
    image_url = _upload(client, recipe["id"], buffer.getvalue(), "big.png").get_json()["image_url"]

    stored = Image.open(os.path.join(app.config["UPLOAD_FOLDER"], image_url.split("/")[-1]))
    assert stored.format == "JPEG" and max(stored.size) == 1200


# Uploading to a recipe that doesn't exist returns 404 and stores nothing.
def test_upload_image_unknown_recipe_returns_404(client, app, jpeg_bytes):
    response = _upload(client, 999, jpeg_bytes)
    assert response.status_code == 404
    assert _files(app) == []


# Uploading without a file returns 400.
def test_upload_image_without_file_returns_400(client):
    recipe = _recipe(client)
    response = client.post(f"/recipes/{recipe['id']}/image", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "No image file" in response.get_json()["error"]


# A file that is not an image is rejected with 400 and nothing is stored.
def test_upload_image_rejects_non_image(client, app):
    recipe = _recipe(client)
    response = _upload(client, recipe["id"], b"this is not an image", "notes.jpg")
    assert response.status_code == 400
    assert _files(app) == []


# If saving to the database fails, the freshly stored file is removed again.
def test_upload_image_db_failure_cleans_up_file(client, app, jpeg_bytes):
    recipe = _recipe(client)
    with patch.object(db.session, "commit", side_effect=RuntimeError("db down")):
        response = _upload(client, recipe["id"], jpeg_bytes)
    assert response.status_code == 500
    assert _files(app) == []


# Deleting the photo clears the URL and removes the file.
def test_delete_image_removes_photo(client, app, jpeg_bytes):
    recipe = _recipe(client)
    _upload(client, recipe["id"], jpeg_bytes)

    response = client.delete(f"/recipes/{recipe['id']}/image")

    assert response.status_code == 200
    assert response.get_json()["image_url"] is None
    assert _files(app) == []


# Deleting the photo of a recipe that has none is fine; an unknown recipe is a 404.
def test_delete_image_without_photo_and_unknown_recipe(client):
    recipe = _recipe(client)
    assert client.delete(f"/recipes/{recipe['id']}/image").status_code == 200
    assert client.delete("/recipes/999/image").status_code == 404


# Deleting a recipe also deletes its photo file.
def test_deleting_recipe_removes_its_photo(client, app, jpeg_bytes):
    recipe = _recipe(client)
    _upload(client, recipe["id"], jpeg_bytes)

    assert client.delete(f"/recipes/{recipe['id']}").status_code == 200
    assert _files(app) == []


# Asking for an image that doesn't exist, or that tries to escape the folder, returns a JSON 404.
def test_get_image_missing_or_traversal_returns_404(client):
    assert client.get("/images/nope.jpg").status_code == 404
    response = client.get("/images/..%2F..%2Fmain.py")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Image not found"


# A request body over the size limit is rejected with a JSON 413.
def test_too_large_upload_returns_413(client, app, jpeg_bytes):
    app.config["MAX_CONTENT_LENGTH"] = 100
    recipe = _recipe(client)
    response = _upload(client, recipe["id"], jpeg_bytes * 10)
    assert response.status_code == 413
    assert "too large" in response.get_json()["error"]
