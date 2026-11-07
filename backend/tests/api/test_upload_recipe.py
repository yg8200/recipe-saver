import io
from unittest.mock import patch

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
    with patch('src.api.upload_recipe.extract_recipe_from_image', return_value=mock_extracted_data) as mock_extract:
        # Create a fake file in memory
        data = {
            'image': (io.BytesIO(b"fake_image_bytes_for_testing"), 'test_recipe.jpg')
        }

        # Send the multipart/form-data request
        response = client.post(
            '/api/recipes/upload',
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


def test_upload_recipe_missing_image_file(client):
    # Send a POST request with no file attached
    response = client.post('/api/recipes/upload')

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "No image file provided"


def test_upload_recipe_empty_filename(client):
    # Send a POST request with a file that has no name
    data = {
        'image': (io.BytesIO(b"empty"), '')
    }
    
    response = client.post(
        '/api/recipes/upload',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Empty file name"


def test_upload_recipe_internal_error(client):
    # Test how the route handles an unexpected error from the AI service
    with patch('src.api.upload_recipe.extract_recipe_from_image', side_effect=Exception("OpenAI API failed")):
        data = {
            'image': (io.BytesIO(b"fake_image_bytes"), 'test.jpg')
        }
        
        response = client.post(
            '/api/recipes/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 500
        assert response.get_json()["error"] == "OpenAI API failed"