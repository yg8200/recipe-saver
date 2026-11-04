def test_delete_recipe_success(client):
    create_payload = {
        "title": "Pancakes",
        "ingredients": ["Flour", "Milk", "Eggs"],
        "instructions": ["Mix ingredients", "Cook on skillet"]
    }
    create_res = client.post("/recipes", json=create_payload)
    assert create_res.status_code == 201
    recipe_id = create_res.get_json()["id"]

    delete_res = client.delete(f"/recipes/{recipe_id}")

    assert delete_res.status_code == 200
    delete_data = delete_res.get_json()
    assert delete_data["message"] == "Recipe deleted successfully"
    assert delete_data["deleted_recipe"]["id"] == recipe_id
    assert delete_data["deleted_recipe"]["title"] == "Pancakes"

    second_delete_res = client.delete(f"/recipes/{recipe_id}")
    assert second_delete_res.status_code == 404


def test_delete_recipe_not_found(client):
    response = client.delete("/recipes/999")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Recipe with id 999 not found"


def test_delete_recipe_invalid_id_type(client):
    response = client.delete("/recipes/not-a-number")

    assert response.status_code == 404