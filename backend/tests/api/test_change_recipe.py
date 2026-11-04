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


def test_update_recipe_not_found(client):
    response = client.put("/recipes/999", json={"title": "Non-existent Recipe"})

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Recipe with id 999 not found"


def test_update_recipe_missing_body(client):
    response = client.put("/recipes/1", data="invalid json", content_type="text/plain")

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Request body must be a valid JSON object"


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