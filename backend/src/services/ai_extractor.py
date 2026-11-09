from src.services.ai_client import get_openai_client, get_openai_model
from src.schemas.recipe_schema import RecipeExtracted


def extract_recipe_from_text(page_text: str) -> RecipeExtracted:
    client = get_openai_client()

    completion = client.beta.chat.completions.parse(
        model=get_openai_model("OPENAI_EXTRACTOR_MODEL"),
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