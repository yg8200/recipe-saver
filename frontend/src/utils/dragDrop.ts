// Drag & drop uses the browser's built-in HTML5 API: a recipe card puts its id into the drag
// payload (dataTransfer), and a folder tile reads it back on drop. A custom MIME type keeps
// unrelated drags (a file from the desktop, selected text) from being treated as a recipe.
export const RECIPE_DRAG_TYPE = 'application/x-recipe-id'
