import pytest


def make_recipe(client, title="Pancakes"):
    response = client.post("/recipes", json={"title": title, "ingredients": ["flour"], "instructions": ["mix"]})
    assert response.status_code == 201
    return response.get_json()["id"]


def make_folder(client, name="Grandma"):
    response = client.post("/folders", json={"name": name})
    assert response.status_code == 201
    return response.get_json()["id"]


# Creating a folder returns it (201) with an empty recipe count; the name is trimmed.
def test_create_folder(client):
    response = client.post("/folders", json={"name": "  Grandma  "})
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Grandma"
    assert body["recipe_count"] == 0


# A bad body or a blank / too long name is rejected with 400.
@pytest.mark.parametrize("payload", [None, [], {}, {"name": "   "}, {"name": 5}, {"name": "x" * 101}])
def test_create_folder_rejects_bad_input(client, payload):
    response = client.post("/folders", json=payload)
    assert response.status_code == 400


# Two folders cannot share a name, ignoring letter case (409).
def test_create_folder_duplicate_name_is_409(client):
    make_folder(client, "Grandma")
    response = client.post("/folders", json={"name": "grandma"})
    assert response.status_code == 409


# The folder list is sorted by name and includes how many recipes each folder holds.
def test_list_folders_sorted_with_counts(client):
    recipe_id = make_recipe(client)
    desserts = make_folder(client, "Desserts")
    make_folder(client, "Breakfast")
    client.put(f"/folders/{desserts}/recipes/{recipe_id}")

    body = client.get("/folders").get_json()
    assert [f["name"] for f in body] == ["Breakfast", "Desserts"]
    assert [f["recipe_count"] for f in body] == [0, 1]


# Renaming works, and renaming to another folder's name is a 409, but keeping its own name is fine.
def test_rename_folder(client):
    first = make_folder(client, "Grandma")
    make_folder(client, "Desserts")

    assert client.patch(f"/folders/{first}", json={"name": "Savta"}).get_json()["name"] == "Savta"
    assert client.patch(f"/folders/{first}", json={"name": "desserts"}).status_code == 409
    assert client.patch(f"/folders/{first}", json={"name": "Savta"}).status_code == 200
    assert client.patch(f"/folders/{first}", json={"name": ""}).status_code == 400
    assert client.patch("/folders/999", json={"name": "x"}).status_code == 404


# A recipe can be in several folders at once, and the recipe reports all its folder ids.
def test_recipe_in_several_folders(client):
    recipe_id = make_recipe(client)
    grandma = make_folder(client, "Grandma")
    desserts = make_folder(client, "Desserts")

    client.put(f"/folders/{desserts}/recipes/{recipe_id}")
    response = client.put(f"/folders/{grandma}/recipes/{recipe_id}")

    assert response.status_code == 200
    assert response.get_json()["folder_ids"] == sorted([grandma, desserts])
    assert client.get(f"/recipes/{recipe_id}").get_json()["folder_ids"] == sorted([grandma, desserts])
    assert client.get("/recipes").get_json()[0]["folder_ids"] == sorted([grandma, desserts])


# Adding the same recipe to a folder twice is a harmless no-op, not an error or a duplicate.
def test_add_recipe_to_folder_is_idempotent(client):
    recipe_id = make_recipe(client)
    folder_id = make_folder(client)

    client.put(f"/folders/{folder_id}/recipes/{recipe_id}")
    response = client.put(f"/folders/{folder_id}/recipes/{recipe_id}")

    assert response.status_code == 200
    assert response.get_json()["folder_ids"] == [folder_id]


# Removing a recipe from a folder keeps the recipe and its other folders; removing again is a no-op.
def test_remove_recipe_from_folder(client):
    recipe_id = make_recipe(client)
    grandma = make_folder(client, "Grandma")
    desserts = make_folder(client, "Desserts")
    client.put(f"/folders/{grandma}/recipes/{recipe_id}")
    client.put(f"/folders/{desserts}/recipes/{recipe_id}")

    response = client.delete(f"/folders/{grandma}/recipes/{recipe_id}")
    assert response.get_json()["folder_ids"] == [desserts]
    assert client.delete(f"/folders/{grandma}/recipes/{recipe_id}").status_code == 200
    assert client.get(f"/recipes/{recipe_id}").status_code == 200


# Linking to a folder or recipe that does not exist is a 404, for both add and remove.
def test_folder_recipe_links_404(client):
    recipe_id = make_recipe(client)
    folder_id = make_folder(client)

    for method in (client.put, client.delete):
        assert method(f"/folders/999/recipes/{recipe_id}").status_code == 404
        assert method(f"/folders/{folder_id}/recipes/999").status_code == 404


# Deleting a folder removes it but NEVER its recipes, which just lose that folder id.
def test_delete_folder_keeps_recipes(client):
    recipe_id = make_recipe(client)
    folder_id = make_folder(client)
    client.put(f"/folders/{folder_id}/recipes/{recipe_id}")

    response = client.delete(f"/folders/{folder_id}")

    assert response.status_code == 200
    assert response.get_json()["deleted_folder"]["name"] == "Grandma"
    assert client.get("/folders").get_json() == []
    assert client.get(f"/recipes/{recipe_id}").get_json()["folder_ids"] == []
    assert client.delete(f"/folders/{folder_id}").status_code == 404


# Deleting a recipe removes it from its folders, so the folder count goes down.
def test_delete_recipe_updates_folder_count(client):
    recipe_id = make_recipe(client)
    folder_id = make_folder(client)
    client.put(f"/folders/{folder_id}/recipes/{recipe_id}")

    client.delete(f"/recipes/{recipe_id}")

    assert client.get("/folders").get_json()[0]["recipe_count"] == 0
