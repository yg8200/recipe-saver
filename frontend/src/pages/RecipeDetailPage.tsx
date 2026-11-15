import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { useDeleteRecipe, useRecipe, useUpdateRecipe } from '../api/recipes'
import FolderPicker from '../components/FolderPicker'
import { secondaryButtonClass } from '../components/RecipeForm'
import StarRating from '../components/StarRating'
import { ErrorMessage, Spinner } from '../components/StatusViews'
import { imageSrc } from '../utils/imageUrl'
import NotFoundPage from './NotFoundPage'

// Section header lines look like "--- לשכבת השקדים ---"; strip the dashes for display
const HEADER = /^-{2,}\s*(.*?)\s*-{2,}$/
const headerText = (line: string) => line.match(HEADER)?.[1] ?? null
// Photo recipes already carry their own "4." prefix. We draw our own number badge instead,
// so strip the prefix to avoid showing the number twice.
// Number of real steps up to and including index i (section headers don't count)
const stepNumber = (lines: string[], i: number) =>
  lines.slice(0, i + 1).filter((l) => headerText(l) === null).length
const stripStepNumber = (line: string) => line.replace(/^\s*\d+\s*[.)]\s*/, '')

export default function RecipeDetailPage() {
  const id = Number(useParams().id) // URL params are always strings
  const { data: recipe, isPending, error, refetch } = useRecipe(id)
  const deleteRecipe = useDeleteRecipe()
  const updateRecipe = useUpdateRecipe(id)
  const navigate = useNavigate()
  // Cooking helpers. They live only in this page (nothing is saved): tick off what you have,
  // mark steps as done. Indexes are positions in the recipe's lists.
  const [haveIngredients, setHaveIngredients] = useState<Set<number>>(new Set())
  const [doneSteps, setDoneSteps] = useState<Set<number>>(new Set())

  if (isPending) return <Spinner />
  if (error instanceof ApiError && error.status === 404) return <NotFoundPage />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />

  function handleDelete(title: string) {
    if (!window.confirm(`למחוק את “${title}”? אי אפשר לבטל את הפעולה.`)) return
    deleteRecipe.mutate(id, { onSuccess: () => navigate('/') })
  }

  const toggle = (set: Set<number>, index: number) => {
    const next = new Set(set)
    if (!next.delete(index)) next.add(index)
    return next
  }
  const realSteps = recipe.instructions.filter((l) => headerText(l) === null).length
  const stats = [
    recipe.prep_time_minutes != null && { label: 'הכנה', value: `${recipe.prep_time_minutes} דק׳` },
    recipe.cook_time_minutes != null && { label: 'בישול', value: `${recipe.cook_time_minutes} דק׳` },
    recipe.servings != null && { label: 'מנות', value: String(recipe.servings) },
  ].filter((s) => s !== false)

  return (
    <article className="space-y-8 sm:space-y-10">
      <div className="flex flex-col gap-4 rounded-xl border border-brand-100 border-t-4 border-t-brand-500 bg-surface p-5 sm:flex-row sm:items-start sm:justify-between sm:p-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:gap-6">
          {recipe.image_url && (
            <img
              src={imageSrc(recipe.image_url)!}
              alt={recipe.title}
              className="aspect-[4/3] w-full rounded-lg object-cover sm:w-72 sm:shrink-0"
            />
          )}
          <div className="space-y-3">
            <Link to="/" className="text-sm text-ink/60 hover:text-ink">
              <span className="inline-block rtl:rotate-180">←</span> כל המתכונים
            </Link>
            <h1 dir="auto" className="text-3xl font-semibold leading-tight sm:text-4xl">{recipe.title}</h1>
            <StarRating value={recipe.rating} onChange={(rating) => updateRecipe.mutate({ rating })} disabled={updateRecipe.isPending} />
            {updateRecipe.error && <ErrorMessage error={updateRecipe.error} />}
            {stats.length > 0 && (
              <dl className="flex flex-wrap gap-x-8 gap-y-2 border-t border-brand-100 pt-3">
                {stats.map((s) => (
                  <div key={s.label}>
                    <dt className="text-xs text-ink/55">{s.label}</dt>
                    <dd className="font-semibold text-brand-700">{s.value}</dd>
                  </div>
                ))}
              </dl>
            )}
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          <Link to={`/recipes/${id}/edit`} className={secondaryButtonClass}>עריכה</Link>
          <button
            onClick={() => handleDelete(recipe.title)}
            disabled={deleteRecipe.isPending}
            className="rounded-lg border border-danger-line bg-surface px-5 py-2.5 pointer-coarse:py-3 text-sm font-medium text-danger transition hover:bg-danger-bg disabled:opacity-60"
          >
            {deleteRecipe.isPending ? 'מוחק…' : 'מחיקה'}
          </button>
        </div>
      </div>

      {deleteRecipe.error && <ErrorMessage error={deleteRecipe.error} />}

      <FolderPicker recipe={recipe} />

      <div className="grid gap-6 sm:gap-8 md:grid-cols-[1fr_2fr]">
        <section className="h-fit rounded-xl border border-herb-100 border-t-4 border-t-herb-500 bg-surface p-5 md:sticky md:top-20">
          <h2 className="mb-4 text-lg font-semibold text-herb-700">מצרכים</h2>
          <ul className="space-y-2">
            {recipe.ingredients.map((line, i) =>
              headerText(line) !== null ? (
                <li key={i} className="pt-2 text-sm font-semibold text-ink/60">{headerText(line)}</li>
              ) : (
                <li key={i} dir="auto">
                  {/* A real checkbox (keyboard + screen reader friendly), "have it" crosses the line out */}
                  <label className="flex cursor-pointer items-start gap-3">
                    <input
                      type="checkbox"
                      checked={haveIngredients.has(i)}
                      onChange={() => setHaveIngredients(toggle(haveIngredients, i))}
                      className="mt-1.5 size-4 shrink-0 accent-brand-600"
                    />
                    <span className={`${haveIngredients.has(i) ? 'text-ink/40 line-through' : ''}`}>{line}</span>
                  </label>
                </li>
              ),
            )}
          </ul>
        </section>

        <section className="rounded-xl border border-brand-100 border-t-4 border-t-brand-500 bg-surface p-5 sm:p-6">
          <div className="mb-4 flex items-baseline justify-between gap-3">
            <h2 className="text-lg font-semibold text-brand-700">אופן הכנה</h2>
            <span className="text-sm text-ink/55">{doneSteps.size} מתוך {realSteps} שלבים הושלמו</span>
          </div>
          <ol className="space-y-3 leading-relaxed">
            {recipe.instructions.map((line, i) =>
              headerText(line) !== null ? (
                <li key={i} className="pt-2 text-sm font-semibold text-ink/60">{headerText(line)}</li>
              ) : (
                <li key={i} dir="auto">
                  {/* The whole step is one button: tap to mark it done (handy with messy hands) */}
                  <button
                    type="button"
                    aria-pressed={doneSteps.has(i)}
                    onClick={() => setDoneSteps(toggle(doneSteps, i))}
                    className={`flex w-full items-start gap-3 rounded-lg p-2 text-start transition hover:bg-brand-50 ${doneSteps.has(i) ? 'opacity-50' : ''}`}
                  >
                    <span aria-hidden className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-md border text-xs font-semibold ${doneSteps.has(i) ? 'border-brand-600 bg-brand-600 text-white' : 'border-brand-500/40 bg-brand-500/10 text-brand-700'}`}>
                      {doneSteps.has(i) ? '✓' : stepNumber(recipe.instructions, i)}
                    </span>
                    <span className={`${doneSteps.has(i) ? 'line-through' : ''}`}>{stripStepNumber(line)}</span>
                  </button>
                </li>
              ),
            )}
          </ol>
        </section>
      </div>
    </article>
  )
}
