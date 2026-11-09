// TypeScript mirror of the backend's Recipe.to_dict() (backend/src/models/recipe.py).
// If the backend shape changes, update it here and TypeScript will point to every place that breaks.
export interface Recipe {
  id: number
  title: string
  ingredients: string[]
  instructions: string[]
  prep_time_minutes: number | null
  cook_time_minutes: number | null
  servings: number | null
  created_at: string | null
}

// Body for creating/updating a recipe: everything except the server-generated fields.
export type RecipeInput = Omit<Recipe, 'id' | 'created_at'>
