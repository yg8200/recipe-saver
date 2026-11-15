import { Link } from 'react-router'
import type { Recipe } from '../api/types'
import { textDirection } from '../utils/textDirection'
import { RECIPE_DRAG_TYPE } from '../utils/dragDrop'
import { imageSrc } from '../utils/imageUrl'

// A small dark label that sits on top of the photo (time, rating)
const chipClass = 'flex items-center gap-1 rounded-lg border border-white/10 bg-black/60 px-2.5 py-1 text-xs font-bold text-white backdrop-blur-md'

// One recipe in the grid on the home page. The whole card is a link to the recipe page.
export default function RecipeCard({ recipe }: { recipe: Recipe }) {
  // Section headers like "--- לשכבת השקדים ---" aren't real ingredients, so skip them
  const ingredients = recipe.ingredients.filter((line) => !line.startsWith('---'))
  const totalMinutes = (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0)

  const facts = [
    recipe.servings != null && (recipe.servings === 1 ? 'מנה אחת' : `${recipe.servings} מנות`),
    `${ingredients.length} מצרכים`,
  ].filter((fact): fact is string => fact !== false)

  return (
    <Link
      to={`/recipes/${recipe.id}`}
      // Drag the card onto a folder tile to add the recipe to that folder. "copy" because the
      // recipe stays where it is (it can be in several folders).
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData(RECIPE_DRAG_TYPE, String(recipe.id))
        e.dataTransfer.effectAllowed = 'copy'
      }}
      dir={textDirection(recipe.title)}
      className="group flex flex-col justify-between overflow-hidden rounded-3xl border border-brand-100 bg-surface shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-brand-600/70 hover:shadow-xl"
    >
      <div>
        {/* Photo with the time and rating on top. Without a photo, a neutral block keeps the grid even. */}
        <div className="relative h-48 overflow-hidden bg-brand-50">
          {recipe.image_url && (
            <img
              src={imageSrc(recipe.image_url)!}
              alt=""
              loading="lazy"
              className="size-full object-cover"
            />
          )}
          <span aria-hidden className="absolute inset-0 bg-gradient-to-t from-[#120e0b]/85 via-transparent to-black/20" />

          <div className="absolute inset-x-3 bottom-3 flex items-center justify-between">
            {totalMinutes > 0 ? (
              <span className={chipClass}>
                <svg aria-hidden viewBox="0 0 24 24" className="size-3.5 text-brand-500" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                  <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
                </svg>
                {totalMinutes} דק׳
              </span>
            ) : <span />}
            {recipe.rating !== null && (
              <span className={`${chipClass} text-amber-400`} role="img" aria-label={`דירוג ${recipe.rating} מתוך 5`}>
                {recipe.rating}
                <svg aria-hidden viewBox="0 0 24 24" className="size-3.5" fill="currentColor">
                  <path d="M12 3.2l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17.2l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z" />
                </svg>
              </span>
            )}
          </div>
        </div>

        <div className="space-y-2 p-4">
          {/* The card's dir (set from the title) mirrors the whole card for Hebrew recipes */}
          <p className="flex items-center gap-2 text-xs font-semibold text-herb-700">
            {facts.map((fact, i) => (
              <span key={fact} className="flex items-center gap-2">
                {i > 0 && <span aria-hidden>•</span>}
                {fact}
              </span>
            ))}
          </p>
          <h2 className="line-clamp-2 font-display text-xl font-bold leading-snug transition-colors group-hover:text-brand-600">{recipe.title}</h2>
          {/* We have no separate description, so the first ingredients act as the teaser */}
          <p dir="auto" className="line-clamp-2 text-xs leading-relaxed text-ink/60">
            {ingredients.slice(0, 4).join(' · ')}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-end border-t border-brand-100 px-4 py-2.5 text-xs">
        <span className="font-bold text-brand-600 transition-transform group-hover:-translate-x-1">פתח מתכון ←</span>
      </div>
    </Link>
  )
}
