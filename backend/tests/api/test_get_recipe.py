# Listing recipes on an empty database returns an empty list.
def test_get_all_recipes_empty(client):
    response = client.get("/recipes")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


# Listing recipes returns every saved recipe.
def test_get_all_recipes_with_data(client):
    client.post("/recipes", json={
        "title": "Salad",
        "ingredients": ["Lettuce", "Cucumber"],
        "instructions": ["Chop and mix"]
    })
    client.post("/recipes", json={
        "title": "Omelette",
        "ingredients": ["Eggs", "Butter"],
        "instructions": ["Whisk and fry"]
    })

    response = client.get("/recipes")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["title"] == "Salad"
    assert data[1]["title"] == "Omelette"


# Fetching a recipe by id returns that recipe.
def test_get_recipe_by_id_success(client):
    create_res = client.post("/recipes", json={
        "title": "Pasta",
        "ingredients": ["Pasta", "Tomato Sauce"],
        "instructions": ["Boil pasta", "Add sauce"]
    })
    recipe_id = create_res.get_json()["id"]

    response = client.get(f"/recipes/{recipe_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == recipe_id
    assert data["title"] == "Pasta"


# Fetching a recipe id that doesn't exist returns 404.
def test_get_recipe_by_id_not_found(client):
    response = client.get("/recipes/999")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Recipe with id 999 not found"


# Fetching with a non-numeric id returns 404.
def test_get_recipe_by_id_invalid_type(client):
    response = client.get("/recipes/invalid-id")

    assert response.status_code == 404