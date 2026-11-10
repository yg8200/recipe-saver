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
      className="group relative flex flex-col gap-3 overflow-hidden rounded-2xl border border-brand-100 bg-surface p-6 pt-7 shadow-sm transition duration-200 hover:-translate-y-1 hover:border-brand-200 hover:shadow-lg hover:shadow-brand-200/40"
    >
      {/* Accent bar along the top edge; it grows on hover. */}
      <span aria-hidden className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-500 to-brand-200 transition-all duration-200 group-hover:h-1.5" />
      {/* The card's dir (set from the title) mirrors the whole card for Hebrew recipes */}
      <h2 className="text-lg font-semibold leading-snug group-hover:text-brand-700">
        {recipe.title}
      </h2>

      <ul dir="auto" className="space-y-0.5 text-sm text-ink/60">
        {preview.map((line, i) => (
          <li key={i} className="truncate before:me-2 before:text-brand-500 before:content-['•']">{line}</li>
        ))}
        {recipe.ingredients.length > preview.length && <li>…</li>}
      </ul>

      <div className="mt-auto">
        <RecipeMeta recipe={recipe} />
      </div>
    </Link>
  )
}
