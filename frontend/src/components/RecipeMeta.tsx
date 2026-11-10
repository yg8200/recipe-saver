import type { Recipe } from '../api/types'

// Prep / cook / servings badges. Fields that are null are simply not shown.
export default function RecipeMeta({ recipe }: { recipe: Recipe }) {
  const items = [
    recipe.prep_time_minutes != null && { icon: '🔪', label: `${recipe.prep_time_minutes} דק׳ הכנה` },
    recipe.cook_time_minutes != null && { icon: '🔥', label: `${recipe.cook_time_minutes} דק׳ בישול` },
    recipe.servings != null && { icon: '🍽️', label: recipe.servings === 1 ? 'מנה אחת' : `${recipe.servings} מנות` },
  ].filter((item) => item !== false)

  if (items.length === 0) return null

  return (
    <ul className="flex flex-wrap gap-2 text-sm">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1 rounded-full bg-herb-50 px-3 py-1 text-herb-700">
          <span aria-hidden>{item.icon}</span>
          {item.label}
        </li>
      ))}
    </ul>
  )
}
