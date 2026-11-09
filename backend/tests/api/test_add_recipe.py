from unittest.mock import patch

import pytest



# Adding a valid recipe saves it and returns 201 with all fields.
def test_add_recipe_success(client):
    payload = {
        "title": "Classic Shakshuka",
        "ingredients": ["Eggs", "Tomatoes", "Peppers", "Garlic", "Cumin"],
        "instructions": ["Saute veggies", "Simmer sauce", "Poach eggs"],
        "prep_time_minutes": 10,
        "cook_time_minutes": 20,
        "servings": 4
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "Classic Shakshuka"
    assert data["ingredients"] == ["Eggs", "Tomatoes", "Peppers", "Garlic", "Cumin"]
    assert data["instructions"] == ["Saute veggies", "Simmer sauce", "Poach eggs"]
    assert data["prep_time_minutes"] == 10
    assert data["cook_time_minutes"] == 20
    assert data["servings"] == 4


# Adding without a JSON body returns 400.
def test_add_recipe_missing_body(client):
    response = client.post("/recipes", data="not json", content_type="text/plain")

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Request body must be a valid JSON object"


# Adding a recipe without a title returns 400.
def test_add_recipe_missing_title(client):
    payload = {
        "ingredients": ["Tomatoes"],
        "instructions": ["Chop"]
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'title' is required" in data["error"]


# Adding a recipe with an empty or whitespace-only title returns 400.
def test_add_recipe_empty_or_whitespace_title(client):
    payload = {
        "title": "   ",
        "ingredients": ["Tomatoes"],
        "instructions": ["Chop"]
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'title' is required" in data["error"]


# Adding a recipe whose title isn't a string returns 400.
def test_add_recipe_invalid_title_type(client):
    payload = {
        "title": 12345,
        "ingredients": ["Tomatoes"],
        "instructions": ["Chop"]
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'title' is required" in data["error"]


# Adding a recipe without ingredients, or with an empty list, returns 400.
def test_add_recipe_missing_or_empty_ingredients(client):
    payload = {
        "title": "Salad",
        "ingredients": [],
        "instructions": ["Toss"]
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'ingredients' is required" in data["error"]


# Adding a recipe whose ingredients aren't a list returns 400.
def test_add_recipe_ingredients_not_a_list(client):
    payload = {
        "title": "Salad",
        "ingredients": "Tomatoes, Cucumbers",
        "instructions": ["Toss"]
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'ingredients' is required" in data["error"]


# Adding a recipe without instructions, or with an empty list, returns 400.
def test_add_recipe_missing_or_empty_instructions(client):
    payload = {
        "title": "Salad",
        "ingredients": ["Lettuce"],
        "instructions": []
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'instructions' is required" in data["error"]


# Each new recipe gets the next id.
def test_add_recipe_sequential_ids(client):
    payload_1 = {
        "title": "Recipe 1",
        "ingredients": ["Water"],
        "instructions": ["Boil"]
    }
    payload_2 = {
        "title": "Recipe 2",
        "ingredients": ["Tea Leaves"],
        "instructions": ["Steep"]
    }

    res_1 = client.post("/recipes", json=payload_1)
    res_2 = client.post("/recipes", json=payload_2)

    assert res_1.status_code == 201
    assert res_2.status_code == 201
    assert res_1.get_json()["id"] == 1
    assert res_2.get_json()["id"] == 2


# A time field sent as text (e.g. "ten") returns 400.
def test_add_recipe_rejects_non_integer_times(client):
    response = client.post("/recipes", json={
        "title": "Bad times", "ingredients": ["a"], "instructions": ["b"], "prep_time_minutes": "ten",
    })
    assert response.status_code == 400


# Adding a recipe whose title already exists (ignoring case and spaces) returns 409 and doesn't save it.
def test_add_recipe_duplicate_title_case_insensitive_returns_409(client):
    payload = {"title": "Hummus", "ingredients": ["Chickpeas"], "instructions": ["Blend"]}
    assert client.post("/recipes", json=payload).status_code == 201

    response = client.post("/recipes", json={**payload, "title": "  hUMMUS  "})

    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]
    assert len(client.get("/recipes").get_json()) == 1


# Spaces around the title are removed before saving.
def test_add_recipe_trims_title(client):
    payload = {"title": "  Falafel  ", "ingredients": ["Chickpeas"], "instructions": ["Fry"]}

    response = client.post("/recipes", json=payload)

    assert response.status_code == 201
    assert response.get_json()["title"] == "Falafel"


# Negative, true/false or decimal values in time/servings fields return 400.
@pytest.mark.parametrize("field, value", [
    ("prep_time_minutes", -1),
    ("cook_time_minutes", True),
    ("servings", 2.5),
])
# Negative, true/false or decimal values in time/servings fields return 400.
def test_add_recipe_rejects_invalid_numeric_fields(client, field, value):
    payload = {"title": "Numbers", "ingredients": ["x"], "instructions": ["y"], field: value}

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    assert field in response.get_json()["error"]


# Time and servings fields may be null.
def test_add_recipe_accepts_null_numeric_fields(client):
    payload = {"title": "No Times", "ingredients": ["x"], "instructions": ["y"],
               "prep_time_minutes": None, "cook_time_minutes": None, "servings": None}

    response = client.post("/recipes", json=payload)

    assert response.status_code == 201
    assert response.get_json()["servings"] is None


# An unexpected database error while saving returns 500 with the error message.
def test_add_recipe_database_error_returns_500(client):
    payload = {"title": "Doomed", "ingredients": ["x"], "instructions": ["y"]}

    with patch("src.api.add_recipe.db.session.commit", side_effect=Exception("DB is down")):
        response = client.post("/recipes", json=payload)

    assert response.status_code == 500
    assert response.get_json()["error"] == "DB is down"
