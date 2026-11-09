import io
from unittest.mock import patch

import pytest

# Uploading an image runs extraction and correction, saves the recipe and returns 201 with the right fields.
def test_upload_recipe_image_success(client):
    # Mock data representing what the AI extractor would return
    mock_extracted_data = {
        "title": "Mocked Pancakes",
        "ingredients": ["1 cup flour", "1 cup milk"],
        "instructions": ["Mix", "Cook on a hot pan"],
        "prep_time": 5,
        "cook_time": 10,
        "servings": 2
    }

    # Patch the extractor function exactly where it is imported in the API route
    # Also patch the AI corrector so the test never calls the real OpenAI API
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=mock_extracted_data) as mock_extract, \
         patch('src.api.upload_recipe.correct_recipe_text', side_effect=lambda data: data):
        # Create a fake file in memory
        data = {
            'image': (io.BytesIO(b"fake_image_bytes_for_testing"), 'test_recipe.jpg')
        }

        # Send the multipart/form-data request
        response = client.post(
            '/recipes/upload',
            data=data,
            content_type='multipart/form-data'
        )

        # Verify the API response
        assert response.status_code == 201
        response_data = response.get_json()
        assert response_data["id"] is not None
        assert response_data["title"] == "Mocked Pancakes"
        assert response_data["prep_time_minutes"] == 5
        assert len(response_data["ingredients"]) == 2
        
        # Verify the mock was called correctly
        mock_extract.assert_called_once()
        args, kwargs = mock_extract.call_args
        assert args[0] == b"fake_image_bytes_for_testing"
        assert args[1] == "image/jpeg"


# Uploading without an 'image' file field returns 400.
def test_upload_recipe_missing_image_file(client):
    # Send a POST request with no file attached
    response = client.post('/recipes/upload')

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "No image file provided"


# Uploading a file with an empty filename returns 400.
def test_upload_recipe_empty_filename(client):
    # Send a POST request with a file that has no name
    data = {
        'image': (io.BytesIO(b"empty"), '')
    }
    
    response = client.post(
        '/recipes/upload',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Empty file name"


# An unexpected error from the image extractor returns 500 with the error message.
def test_upload_recipe_internal_error(client):
    # Test how the route handles an unexpected error from the AI service
    with patch('src.api.upload_recipe.extract_recipe_from_image', side_effect=Exception("OpenAI API failed")):
        data = {
            'image': (io.BytesIO(b"fake_image_bytes"), 'test.jpg')
        }
        
        response = client.post(
            '/recipes/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 500
        assert response.get_json()["error"] == "OpenAI API failed"

# Uploading bytes that aren't a real image returns 400 (not a server error).
def test_upload_recipe_invalid_image_returns_400(client):
    # Real (unmocked) image processing should reject bytes that are not an image
    data = {'image': (io.BytesIO(b"definitely not an image"), 'test.jpg')}
    response = client.post('/recipes/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 400


# If the AI corrector crashes, the uncorrected OCR text is saved instead of failing the upload.
def test_upload_recipe_saves_raw_ocr_when_corrector_fails(client):
    raw = {"title": "Raw Cake", "ingredients": ["flour"], "instructions": ["bake"], "cook_time": 30}
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=raw), \
         patch('src.api.upload_recipe.correct_recipe_text', side_effect=Exception("OpenAI down")):
        data = {'image': (io.BytesIO(b"img"), 'test.jpg')}
        response = client.post('/recipes/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 201
    assert response.get_json()["title"] == "Raw Cake"
    assert response.get_json()["cook_time_minutes"] == 30


# If the AI corrector returns JSON in the wrong shape, the uncorrected OCR text is saved instead.
def test_upload_recipe_saves_raw_ocr_when_corrector_breaks_structure(client):
    raw = {"title": "Raw Bread", "ingredients": ["flour"], "instructions": ["knead"]}
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=raw), \
         patch('src.api.upload_recipe.correct_recipe_text', return_value={"recipe": "oops"}):
        data = {'image': (io.BytesIO(b"img"), 'test.jpg')}
        response = client.post('/recipes/upload', data=data, content_type='multipart/form-data')

    assert response.status_code == 201
    assert response.get_json()["title"] == "Raw Bread"


RAW_OCR = {"title": "Raw Cake", "ingredients": ["flour"], "instructions": ["bake"]}


def _upload(client, filename="test.jpg", content_type=None, payload=b"img"):
    file = (io.BytesIO(payload), filename, content_type) if content_type else (io.BytesIO(payload), filename)
    return client.post('/recipes/upload', data={'image': file}, content_type='multipart/form-data')


# A .heic/.heif filename is treated as image/heic even if the browser sent a generic content type.
@pytest.mark.parametrize("filename", ["photo.HEIC", "photo.heif"])
def test_upload_recipe_detects_heic_from_filename(client, filename):
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=RAW_OCR) as extract, \
         patch('src.api.upload_recipe.correct_recipe_text', side_effect=lambda d: d):
        response = _upload(client, filename, content_type="application/octet-stream")

    assert response.status_code == 201
    assert extract.call_args.args[1] == "image/heic"


# When the corrector succeeds, its corrected text (not the raw OCR) is what gets saved.
def test_upload_recipe_uses_corrected_text(client):
    corrected = {**RAW_OCR, "title": "Corrected Cake"}
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=RAW_OCR), \
         patch('src.api.upload_recipe.correct_recipe_text', return_value=corrected):
        response = _upload(client)

    assert response.status_code == 201
    assert response.get_json()["title"] == "Corrected Cake"


# If the corrector returns something that isn't a dict, the raw OCR text is saved.
def test_upload_recipe_falls_back_when_corrector_returns_non_dict(client):
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=RAW_OCR), \
         patch('src.api.upload_recipe.correct_recipe_text', return_value=["not", "a", "dict"]):
        response = _upload(client)

    assert response.status_code == 201
    assert response.get_json()["title"] == "Raw Cake"


# Uploading a recipe whose title already exists (case-insensitive) returns 409.
def test_upload_recipe_duplicate_title_returns_409(client):
    client.post("/recipes", json={"title": "raw cake", "ingredients": ["a"], "instructions": ["b"]})

    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=RAW_OCR), \
         patch('src.api.upload_recipe.correct_recipe_text', side_effect=lambda d: d):
        response = _upload(client)

    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


# An image with no ingredients/instructions returns 400 and nothing is saved.
def test_upload_recipe_without_recipe_in_image_returns_400_and_saves_nothing(client):
    no_recipe = {"title": "Random photo", "ingredients": [], "instructions": []}
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=no_recipe), \
         patch('src.api.upload_recipe.correct_recipe_text', side_effect=lambda d: d):
        response = _upload(client)

    assert response.status_code == 400
    assert client.get("/recipes").get_json() == []


# A valid image with no GEMINI_API_KEY configured returns 500 naming the missing key.
def test_upload_recipe_missing_gemini_key_returns_500(client):
    # A real (tiny) PNG passes image processing, then the blank GEMINI_API_KEY stops the AI call
    from PIL import Image
    png = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(png, format="PNG")

    response = _upload(client, "real.png", payload=png.getvalue())

    assert response.status_code == 500
    assert "GEMINI_API_KEY" in response.get_json()["error"]
