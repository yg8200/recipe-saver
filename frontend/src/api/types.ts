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
  image_url: string | null // path of the dish photo, e.g. "/images/ab12.jpg", or null
  folder_ids: number[] // ids of the folders this recipe is in (a recipe can be in several)
  created_at: string | null
}

// Body for creating/updating a recipe: everything except the server-generated fields.
export type RecipeInput = Omit<Recipe, 'id' | 'created_at' | 'image_url' | 'folder_ids'>

// A named collection of recipes (e.g. "Grandma's dishes"). Mirrors Folder.to_dict() in the backend.
export interface Folder {
  id: number
  name: string
  recipe_count: number
  created_at: string | null
}
