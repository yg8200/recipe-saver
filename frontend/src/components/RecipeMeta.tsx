import type { Recipe } from '../api/types'

// Prep / cook / servings badges. Fields that are null are simply not shown.
export default function RecipeMeta({ recipe }: { recipe: Recipe }) {
  const items = [
    recipe.prep_time_minutes != null && { icon: '🔪', label: `${recipe.prep_time_minutes} min prep` },
    recipe.cook_time_minutes != null && { icon: '🔥', label: `${recipe.cook_time_minutes} min cook` },
    recipe.servings != null && { icon: '🍽️', label: `${recipe.servings} servings` },
  ].filter((item) => item !== false)

  if (items.length === 0) return null

  return (
    <ul className="flex flex-wrap gap-2 text-sm">
      {items.map((item) => (
        // dir="ltr": the badge text is English UI ("14 min cook"). Inside a Hebrew (RTL) recipe the
        // browser would otherwise reorder it to "min cook 14". The badges still line up from the right.
        <li key={item.label} dir="ltr" className="flex items-center gap-1 rounded-full bg-herb-50 px-3 py-1 text-herb-700">
          <span aria-hidden>{item.icon}</span>
          {item.label}
        </li>
      ))}
    </ul>
  )
}
