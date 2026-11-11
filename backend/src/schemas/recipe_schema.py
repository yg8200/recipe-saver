from pydantic import BaseModel, Field


class RecipeExtracted(BaseModel):
    title: str = Field(description="The primary name of the recipe")
    ingredients: list[str] = Field(
        description=(
            "Ingredients including quantities and units. If the recipe groups them under headings "
            "(e.g. dough / topping), put a line '--- heading ---' before each group."
        )
    )
    instructions: list[str] = Field(
        description=(
            "Sequential preparation and cooking steps. If the recipe groups steps under headings, "
            "put a line '--- heading ---' before each group."
        )
    )
    prep_time_minutes: int | None = Field(
        default=None,
        description="Prep time in minutes, or null if not mentioned",
    )
    cook_time_minutes: int | None = Field(
        default=None,
        description="Cooking or baking time in minutes, or null if not mentioned",
    )
    servings: int | None = Field(
        default=None,
        description="Number of servings or yield, or null if not mentioned",
    )