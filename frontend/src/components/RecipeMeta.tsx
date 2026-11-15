import type { Recipe } from '../api/types'

// Prep / cook / servings as one quiet line of text. Fields that are null are simply not shown.
export default function RecipeMeta({ recipe }: { recipe: Recipe }) {
  const items = [
    recipe.prep_time_minutes != null && `${recipe.prep_time_minutes} דק׳ הכנה`,
    recipe.cook_time_minutes != null && `${recipe.cook_time_minutes} דק׳ בישול`,
    recipe.servings != null && (recipe.servings === 1 ? 'מנה אחת' : `${recipe.servings} מנות`),
  ].filter((item): item is string => item !== false)

  if (items.length === 0) return null

  return (
    <ul className="flex flex-wrap gap-x-2 gap-y-1 text-sm text-ink/60">
      {items.map((label, i) => (
        <li key={label} className="flex gap-2">
          {i > 0 && <span aria-hidden className="text-ink/30">·</span>}
          {label}
        </li>
      ))}
    </ul>
  )
}
