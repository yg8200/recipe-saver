import { Link } from 'react-router'
import type { Recipe } from '../api/types'
import { textDirection } from '../utils/textDirection'
import RecipeMeta from './RecipeMeta'

// One recipe in the grid on the home page. The whole card is a link to the recipe page.
export default function RecipeCard({ recipe }: { recipe: Recipe }) {
  // Section headers like "--- לשכבת השקדים ---" aren't real ingredients, so skip them in the preview
  const preview = recipe.ingredients.filter((line) => !line.startsWith('---')).slice(0, 3)

  return (
    <Link
      to={`/recipes/${recipe.id}`}
      dir={textDirection(recipe.title)}
      className="group flex flex-col gap-3 rounded-2xl border border-brand-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      {/* The card's dir (set from the title) mirrors the whole card for Hebrew recipes */}
      <h2 className="text-lg font-semibold leading-snug group-hover:text-brand-700">
        {recipe.title}
      </h2>

      <ul dir="auto" className="space-y-0.5 text-sm text-ink/60">
        {preview.map((line, i) => (
          <li key={i} className="truncate">{line}</li>
        ))}
        {recipe.ingredients.length > preview.length && <li>…</li>}
      </ul>

      <div className="mt-auto">
        <RecipeMeta recipe={recipe} />
      </div>
    </Link>
  )
}
