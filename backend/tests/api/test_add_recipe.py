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


def test_add_recipe_missing_body(client):
    response = client.post("/recipes", data="not json", content_type="text/plain")

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Request body must be a valid JSON object"


def test_add_recipe_missing_title(client):
    payload = {
        "ingredients": ["Tomatoes"],
        "instructions": ["Chop"]
    }

    response = client.post("/recipes", json=payload)

    assert response.status_code == 400
    data = response.get_json()
    assert "'title' is required" in data["error"]


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