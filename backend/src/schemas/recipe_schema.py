from pydantic import BaseModel, Field


class RecipeExtracted(BaseModel):
    title: str = Field(description="The primary name of the recipe")
    ingredients: list[str] = Field(
        description="List of ingredients including quantities and units"
    )
    instructions: list[str] = Field(
        description="Sequential preparation and cooking steps"
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