from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError



# PUT with all fields replaces every field of an existing recipe.
def test_update_recipe_full_success(client):
    create_payload = {
        "title": "Plain Toast",
        "ingredients": ["Bread"],
        "instructions": ["Toast bread"],
        "prep_time_minutes": 1,
        "cook_time_minutes": 3,
        "servings": 1
    }
    create_res = client.post("/recipes", json=create_payload)
    assert create_res.status_code == 201
    recipe_id = create_res.get_json()["id"]

    update_payload = {
        "title": "Avocado Toast",
        "ingredients": ["Bread", "Avocado", "Salt", "Chili Flakes"],
        "instructions": ["Toast bread", "Mash avocado with salt", "Spread and garnish"],
        "prep_time_minutes": 5,
        "cook_time_minutes": 3,
        "servings": 2
    }
    update_res = client.put(f"/recipes/{recipe_id}", json=update_payload)

    assert update_res.status_code == 200
    updated_data = update_res.get_json()
    assert updated_data["id"] == recipe_id
    assert updated_data["title"] == "Avocado Toast"
    assert len(updated_data["ingredients"]) == 4
    assert updated_data["servings"] == 2


# PATCH with some fields updates only those fields and keeps the rest.
def test_update_recipe_partial_patch_success(client):
    create_payload = {
        "title": "Quick Soup",
        "ingredients": ["Broth", "Noodles"],
        "instructions": ["Boil broth", "Add noodles"],
        "cook_time_minutes": 10
    }
    create_res = client.post("/recipes", json=create_payload)
    recipe_id = create_res.get_json()["id"]

    patch_payload = {
        "cook_time_minutes": 15
    }
    patch_res = client.patch(f"/recipes/{recipe_id}", json=patch_payload)

    assert patch_res.status_code == 200
    data = patch_res.get_json()
    assert data["id"] == recipe_id
    assert data["cook_time_minutes"] == 15
    assert data["title"] == "Quick Soup"
    assert data["ingredients"] == ["Broth", "Noodles"]


# Updating a recipe id that doesn't exist returns 404.
def test_update_recipe_not_found(client):
    response = client.put("/recipes/999", json={"title": "Non-existent Recipe"})

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Recipe with id 999 not found"


# Updating without a JSON body returns 400.
def test_update_recipe_missing_body(client):
    response = client.put("/recipes/1", data="invalid json", content_type="text/plain")

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Request body must be a valid JSON object"


# Updating the title to an empty/whitespace string returns 400.
def test_update_recipe_invalid_title(client):
    create_res = client.post("/recipes", json={
        "title": "Salad",
        "ingredients": ["Lettuce"],
        "instructions": ["Toss"]
    })
    recipe_id = create_res.get_json()["id"]

    response = client.patch(f"/recipes/{recipe_id}", json={"title": "   "})

    assert response.status_code == 400
    data = response.get_json()
    assert "'title' must be a non-empty string" in data["error"]


# Updating ingredients to an empty list or non-list returns 400.
def test_update_recipe_invalid_ingredients(client):
    create_res = client.post("/recipes", json={
        "title": "Salad",
        "ingredients": ["Lettuce"],
        "instructions": ["Toss"]
    })
    recipe_id = create_res.get_json()["id"]

    response = client.patch(f"/recipes/{recipe_id}", json={"ingredients": []})

    assert response.status_code == 400
    data = response.get_json()
    assert "'ingredients' must be a non-empty list" in data["error"]


# Updating a time/servings field to a non-integer or negative value returns 400.
def test_update_recipe_invalid_numeric_field(client):
    create_res = client.post("/recipes", json={
        "title": "Salad",
        "ingredients": ["Lettuce"],
        "instructions": ["Toss"]
    })
    recipe_id = create_res.get_json()["id"]

    response = client.patch(f"/recipes/{recipe_id}", json={"prep_time_minutes": -5})

    assert response.status_code == 400
    data = response.get_json()
    assert "'prep_time_minutes' must be a non-negative integer or null" in data["error"]

# Renaming a recipe to another recipe's title (case-insensitive) returns 409.
def test_update_recipe_title_to_existing_title_returns_409(client):
    payload = {"ingredients": ["a"], "instructions": ["b"]}
    client.post("/recipes", json={"title": "First", **payload})
    second = client.post("/recipes", json={"title": "Second", **payload}).get_json()
    response = client.patch(f"/recipes/{second['id']}", json={"title": "first"})
    assert response.status_code == 409


def _create(client, title="Base Recipe"):
    response = client.post("/recipes", json={"title": title, "ingredients": ["a"], "instructions": ["b"]})
    assert response.status_code == 201
    return response.get_json()["id"]


# Updating instructions to an empty list, a string or null returns 400.
@pytest.mark.parametrize("value", [[], "not a list", None])
def test_update_recipe_invalid_instructions(client, value):
    recipe_id = _create(client)

    response = client.patch(f"/recipes/{recipe_id}", json={"instructions": value})

    assert response.status_code == 400
    assert "'instructions' must be a non-empty list" in response.get_json()["error"]


# A recipe can be updated with its own title (even in different case) without a duplicate error.
def test_update_recipe_keeping_its_own_title_is_allowed(client):
    recipe_id = _create(client, "Same Title")

    response = client.patch(f"/recipes/{recipe_id}", json={"title": "same title", "servings": 2})

    assert response.status_code == 200
    assert response.get_json()["title"] == "same title"


# A time/servings field can be cleared by sending null.
def test_update_recipe_can_clear_numeric_field(client):
    recipe_id = client.post("/recipes", json={
        "title": "Timed", "ingredients": ["a"], "instructions": ["b"], "cook_time_minutes": 10,
    }).get_json()["id"]

    response = client.patch(f"/recipes/{recipe_id}", json={"cook_time_minutes": None})

    assert response.status_code == 200
    assert response.get_json()["cook_time_minutes"] is None


# If any field is invalid, none of the other fields in the request are applied.
def test_update_recipe_failed_validation_does_not_save_partial_changes(client):
    recipe_id = _create(client, "Untouched")

    response = client.patch(f"/recipes/{recipe_id}", json={"title": "Changed", "servings": -5})

    assert response.status_code == 400
    assert client.get(f"/recipes/{recipe_id}").get_json()["title"] == "Untouched"


# A unique-title conflict caught by the database at commit time returns 409 (race-condition safety net).
def test_update_recipe_integrity_error_on_commit_returns_409(client):
    recipe_id = _create(client)

    with patch("src.api.change_recipe.db.session.commit",
               side_effect=IntegrityError("UPDATE", {}, Exception("unique constraint"))):
        response = client.patch(f"/recipes/{recipe_id}", json={"title": "Race Condition"})

    assert response.status_code == 409


# An unexpected database error while saving an update returns 500 with the error message.
def test_update_recipe_database_error_returns_500(client):
    recipe_id = _create(client)

    with patch("src.api.change_recipe.db.session.commit", side_effect=Exception("DB is down")):
        response = client.patch(f"/recipes/{recipe_id}", json={"servings": 3})

    assert response.status_code == 500
    assert response.get_json()["error"] == "DB is down"
