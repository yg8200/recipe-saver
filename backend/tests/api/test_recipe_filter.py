import pytest


def make_recipe(client, title, rating=None):
    """Create a recipe and, if a rating is given, rate it (POST /recipes ignores 'rating', PATCH sets it)."""
    recipe_id = client.post(
        "/recipes", json={"title": title, "ingredients": ["x"], "instructions": ["mix"]}
    ).get_json()["id"]
    if rating is not None:
        client.patch(f"/recipes/{recipe_id}", json={"rating": rating})
    return recipe_id


def titles_for(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return [recipe["title"] for recipe in response.get_json()]


def make_sample_recipes(client):
    """Four recipes with fixed ratings, so every run gives the same result."""
    make_recipe(client, "Pancakes", 3)
    make_recipe(client, "Shakshuka", 4)
    make_recipe(client, "Pasta", 5)
    make_recipe(client, "Pizza")  # not rated


# Filtering when there are no recipes at all returns 200 and an empty list.
def test_filter_with_no_recipes_returns_empty_list(client):
    response = client.get("/recipes?min_rating=3")
    assert response.status_code == 200
    assert response.get_json() == []


# Without the min_rating parameter every recipe comes back, including the unrated one.
def test_no_filter_returns_all_recipes_including_unrated(client):
    make_sample_recipes(client)
    assert titles_for(client, "/recipes") == ["Pancakes", "Shakshuka", "Pasta", "Pizza"]


# min_rating=4 returns exactly the recipes rated 4 or higher, oldest first.
def test_filter_returns_only_recipes_at_or_above_the_rating(client):
    make_sample_recipes(client)
    assert titles_for(client, "/recipes?min_rating=4") == ["Shakshuka", "Pasta"]


# The limit values are inclusive: min_rating=5 keeps the 5-star recipe, and min_rating=1 keeps every rated one.
def test_filter_limits_are_inclusive_and_unrated_recipes_are_left_out(client):
    make_sample_recipes(client)
    assert titles_for(client, "/recipes?min_rating=5") == ["Pasta"]
    assert titles_for(client, "/recipes?min_rating=1") == ["Pancakes", "Shakshuka", "Pasta"]


# A filter that nothing matches returns an empty list, not an error.
def test_filter_with_no_match_returns_empty_list(client):
    make_recipe(client, "Pancakes", 3)
    assert titles_for(client, "/recipes?min_rating=5") == []


# A min_rating that is not a whole number from 1 to 5 is rejected with 400 and a clear message.
@pytest.mark.parametrize("bad", ["abc", "0", "6", "-1", "3.5", ""])
def test_filter_with_invalid_rating_returns_400(client, bad):
    response = client.get(f"/recipes?min_rating={bad}")
    assert response.status_code == 400
    assert response.get_json()["error"] == "'min_rating' must be an integer from 1 to 5"
