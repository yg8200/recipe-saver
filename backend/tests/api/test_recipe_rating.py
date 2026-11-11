import pytest


def make_recipe(client):
    response = client.post("/recipes", json={"title": "Pancakes", "ingredients": ["flour"], "instructions": ["mix"]})
    return response.get_json()["id"]


# A new recipe starts unrated (rating is null).
def test_new_recipe_has_no_rating(client):
    recipe_id = make_recipe(client)
    assert client.get(f"/recipes/{recipe_id}").get_json()["rating"] is None


# Any rating from 1 to 5 can be saved with PATCH and is returned by later reads.
@pytest.mark.parametrize("stars", [1, 2, 3, 4, 5])
def test_set_rating(client, stars):
    recipe_id = make_recipe(client)
    response = client.patch(f"/recipes/{recipe_id}", json={"rating": stars})
    assert response.status_code == 200
    assert response.get_json()["rating"] == stars
    assert client.get(f"/recipes/{recipe_id}").get_json()["rating"] == stars


# Sending null removes the rating again.
def test_clear_rating(client):
    recipe_id = make_recipe(client)
    client.patch(f"/recipes/{recipe_id}", json={"rating": 4})
    response = client.patch(f"/recipes/{recipe_id}", json={"rating": None})
    assert response.status_code == 200
    assert response.get_json()["rating"] is None


# Anything that is not a whole number from 1 to 5 is rejected with 400 and nothing is saved.
@pytest.mark.parametrize("bad", [0, 6, -1, 3.5, "5", True, [], {}])
def test_invalid_rating_is_rejected(client, bad):
    recipe_id = make_recipe(client)
    client.patch(f"/recipes/{recipe_id}", json={"rating": 3})
    response = client.patch(f"/recipes/{recipe_id}", json={"rating": bad})
    assert response.status_code == 400
    assert client.get(f"/recipes/{recipe_id}").get_json()["rating"] == 3


# Editing other fields (what the edit form does) leaves the rating untouched.
def test_editing_other_fields_keeps_rating(client):
    recipe_id = make_recipe(client)
    client.patch(f"/recipes/{recipe_id}", json={"rating": 5})
    client.patch(f"/recipes/{recipe_id}", json={"title": "Better Pancakes"})
    assert client.get(f"/recipes/{recipe_id}").get_json()["rating"] == 5
