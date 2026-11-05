import os
from openai import OpenAI
from src.schemas.recipe_schema import RecipeExtracted


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def extract_recipe_from_text(page_text: str) -> RecipeExtracted:
    client = get_openai_client()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a structured culinary data extraction engine. "
                    "Analyze the provided recipe webpage text and extract the "
                    "title, ingredients, instructions, and cooking times accurately."
                ),
            },
            {"role": "user", "content": page_text},
        ],
        response_format=RecipeExtracted,
    )

    return completion.choices[0].message.parsed