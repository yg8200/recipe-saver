# Getting a random recipe when there are no recipes in the db returns 404 with a clear message.
def test_get_random_recipe_0_recipes(client):
    response = client.get("/recipes/random")
    assert response.status_code == 404
    assert response.get_json()["error"] == "No recipes found"


# Getting a random recipe when there is exactly one in the db returns that recipe.
def test_get_random_recipe_one(client):
    client.post("/recipes", json={"title": "Pancakes", "ingredients": ["flour"], "instructions": ["mix"]})
    response = client.get("/recipes/random")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Pancakes"


# Getting a random recipe when there are several always returns one of the saved recipes.
def test_get_random_recipe_many(client):
    titles = ["Pancakes", "Shakshuka", "Pasta", "Pizza"]
    for title in titles:
        client.post("/recipes", json={"title": title, "ingredients": ["x"], "instructions": ["mix"]})
    # One call can't tell "random" from "always the first", so ask several times
    for _ in range(10):
        response = client.get("/recipes/random")
        assert response.status_code == 200
        assert response.get_json()["title"] in titles
