import { Link, useNavigate, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { useDeleteRecipe, useRecipe, useUpdateRecipe } from '../api/recipes'
import FolderPicker from '../components/FolderPicker'
import { dangerButtonClass, secondaryButtonClass } from '../components/RecipeForm'
import StarRating from '../components/StarRating'
import { ErrorMessage, Spinner } from '../components/StatusViews'
import { imageSrc } from '../utils/imageUrl'
import { clearStoredSet, useStoredSet } from '../utils/useStoredSet'
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

const Check = () => (
  <svg aria-hidden viewBox="0 0 24 24" className="size-3.5" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m5 12 5 5 9-10" />
  </svg>
)
const ClockIcon = () => (
  <svg aria-hidden viewBox="0 0 24 24" className="size-3.5 text-brand-600" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
    <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
  </svg>
)
const FlameIcon = () => (
  <svg aria-hidden viewBox="0 0 24 24" className="size-3.5 text-brand-600" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3c1 3.5 5 5.5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 .3 1.2 1 2 2 2 0-3-1-5 1-8z" />
  </svg>
)
const UsersIcon = () => (
  <svg aria-hidden viewBox="0 0 24 24" className="size-3.5 text-herb-700" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
    <circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 3.5 6" />
  </svg>
)

export default function RecipeDetailPage() {
  const id = Number(useParams().id) // URL params are always strings
  const { data: recipe, isPending, error, refetch } = useRecipe(id)
  const deleteRecipe = useDeleteRecipe()
  const updateRecipe = useUpdateRecipe(id)
  const navigate = useNavigate()
  // Cooking helpers: tick off what you have, mark steps as done. They are saved in this browser
  // (per recipe), so they are still there when you come back. Indexes are positions in the lists.
  const ingredientsKey = `recipe-${id}-ingredients`
  const stepsKey = `recipe-${id}-steps`
  const [haveIngredients, setHaveIngredients] = useStoredSet(ingredientsKey)
  const [doneSteps, setDoneSteps] = useStoredSet(stepsKey)

  if (isPending) return <Spinner />
  if (error instanceof ApiError && error.status === 404) return <NotFoundPage />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />

  function handleDelete(title: string) {
    if (!window.confirm(`למחוק את “${title}”? אי אפשר לבטל את הפעולה.`)) return
    deleteRecipe.mutate(id, {
      onSuccess: () => {
        clearStoredSet(ingredientsKey)
        clearStoredSet(stepsKey)
        navigate('/')
      },
    })
  }

  const toggle = (set: Set<number>, index: number) => {
    const next = new Set(set)
    if (!next.delete(index)) next.add(index)
    return next
  }
  const realSteps = recipe.instructions.filter((l) => headerText(l) === null).length
  const stats = [
    recipe.prep_time_minutes != null && { label: 'הכנה', value: `${recipe.prep_time_minutes} דק׳`, icon: <ClockIcon /> },
    recipe.cook_time_minutes != null && { label: 'בישול', value: `${recipe.cook_time_minutes} דק׳`, icon: <FlameIcon /> },
    recipe.servings != null && { label: 'מנות', value: String(recipe.servings), icon: <UsersIcon /> },
  ].filter((s) => s !== false)

  return (
    <article className="space-y-6">
      {/* Top bar: back link on one side, edit / delete on the other */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-bold text-ink/60 transition hover:text-brand-600">
          <span className="inline-block rtl:rotate-180">←</span> כל המתכונים
        </Link>
        <div className="flex items-center gap-2">
          <Link to={`/recipes/${id}/edit`} className={`${secondaryButtonClass} !px-4 !py-2 text-xs`}>עריכה</Link>
          <button
            onClick={() => handleDelete(recipe.title)}
            disabled={deleteRecipe.isPending}
            className={`${dangerButtonClass} !px-4 !py-2 text-xs`}
          >
            {deleteRecipe.isPending ? 'מוחק…' : 'מחיקה'}
          </button>
        </div>
      </div>

      {deleteRecipe.error && <ErrorMessage error={deleteRecipe.error} />}

      {/* Hero: title, rating and facts on one side, the photo on the other */}
      <section className="grid items-center gap-7 rounded-3xl border border-brand-100 bg-gradient-to-br from-surface to-brand-50 p-6 shadow-lg sm:p-8 lg:grid-cols-12 dark:from-surface dark:to-surface">
        <div className={`space-y-5 ${recipe.image_url ? 'lg:col-span-7' : 'lg:col-span-12'}`}>
          <div className="flex flex-wrap items-center gap-2">
            <StarRating value={recipe.rating} onChange={(rating) => updateRecipe.mutate({ rating })} disabled={updateRecipe.isPending} />
            {recipe.rating !== null && <span className="text-xs font-bold text-ink/60">({recipe.rating}/5)</span>}
          </div>
          {updateRecipe.error && <ErrorMessage error={updateRecipe.error} />}

          <h1 dir="auto" className="font-display text-4xl font-extrabold leading-tight sm:text-5xl">{recipe.title}</h1>

          {stats.length > 0 && (
            <dl className="grid grid-cols-3 gap-3 border-t border-brand-100 pt-4">
              {stats.map((s) => (
                <div key={s.label} className="rounded-2xl border border-brand-100 bg-brand-50 p-3.5">
                  <dt className="mb-1 flex items-center gap-1 text-sm text-ink/55">{s.icon}{s.label}</dt>
                  <dd className="text-lg font-extrabold text-brand-700 sm:text-xl">{s.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>

        {recipe.image_url && (
          <div className="lg:col-span-5">
            <img
              src={imageSrc(recipe.image_url)!}
              alt={recipe.title}
              className="aspect-[4/3] w-full rounded-2xl border border-amber-200/15 object-cover shadow-xl"
            />
          </div>
        )}
      </section>

      <FolderPicker recipe={recipe} />

      {/* Cooking workspace: ingredients on one side, steps on the other */}
      <div className="grid items-start gap-6 lg:grid-cols-12">
        <section className="overflow-hidden rounded-3xl border border-herb-100 bg-herb-50 shadow-md lg:sticky lg:top-24 lg:col-span-5 dark:border-brand-100 dark:bg-surface">
          <div className="h-1.5 w-full bg-gradient-to-l from-herb-500 to-[#56a87d]" />
          <div className="space-y-4 p-6">
            <h2 className="text-xl font-extrabold text-herb-700">מצרכים</h2>
            <ul className="space-y-1.5">
              {recipe.ingredients.map((line, i) =>
                headerText(line) !== null ? (
                  <li key={i} className="px-2.5 pt-2 text-base font-bold text-ink/60">{headerText(line)}</li>
                ) : (
                  <li key={i} dir="auto">
                    {/* A real checkbox (keyboard + screen reader friendly); "have it" crosses the line out */}
                    <label className={`flex cursor-pointer select-none items-center gap-3 rounded-xl p-2.5 transition hover:bg-brand-50 ${haveIngredients.has(i) ? 'opacity-55' : ''}`}>
                      <input
                        type="checkbox"
                        checked={haveIngredients.has(i)}
                        onChange={() => setHaveIngredients(toggle(haveIngredients, i))}
                        className="peer sr-only"
                      />
                      <span className={`grid size-5 shrink-0 place-items-center rounded-md border text-white transition peer-focus-visible:ring-2 peer-focus-visible:ring-brand-600 ${haveIngredients.has(i) ? 'border-herb-500 bg-herb-500' : 'border-brand-200 bg-field'}`}>
                        {haveIngredients.has(i) && <Check />}
                      </span>
                      <span className={`text-base leading-snug ${haveIngredients.has(i) ? 'line-through' : ''}`}>{line}</span>
                    </label>
                  </li>
                ),
              )}
            </ul>
          </div>
        </section>

        <section className="overflow-hidden rounded-3xl border border-brand-100 bg-brand-50/70 shadow-md lg:col-span-7 dark:bg-surface">
          <div className="h-1.5 w-full bg-gradient-to-l from-brand-600 to-brand-500" />
          <div className="space-y-5 p-6 sm:p-7">
            <div className="space-y-2.5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-xl font-extrabold text-brand-700">אופן הכנה</h2>
                <span className="flex items-center gap-3 text-sm font-semibold text-ink/50">
                  {doneSteps.size} מתוך {realSteps} שלבים הושלמו
                  {(doneSteps.size > 0 || haveIngredients.size > 0) && (
                    <button
                      type="button"
                      onClick={() => { setDoneSteps(new Set()); setHaveIngredients(new Set()) }}
                      className="text-brand-600 underline-offset-2 hover:underline"
                    >
                      ניקוי סימונים
                    </button>
                  )}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-brand-50">
                <div
                  className="h-full bg-gradient-to-l from-brand-600 to-herb-700 transition-all duration-300"
                  style={{ width: `${(doneSteps.size / Math.max(1, realSteps)) * 100}%` }}
                />
              </div>
            </div>

            <ol className="space-y-3.5">
              {recipe.instructions.map((line, i) =>
                headerText(line) !== null ? (
                  <li key={i} className="pt-2 text-base font-bold text-ink/60">{headerText(line)}</li>
                ) : (
                  <li key={i} dir="auto">
                    {/* The whole step is one button: tap to mark it done (handy with messy hands) */}
                    <button
                      type="button"
                      aria-pressed={doneSteps.has(i)}
                      onClick={() => setDoneSteps(toggle(doneSteps, i))}
                      className={`flex w-full items-start gap-3.5 rounded-2xl border p-4 text-start transition ${doneSteps.has(i) ? 'border-transparent bg-brand-50 opacity-60' : 'border-brand-100 hover:border-brand-600/50'}`}
                    >
                      <span aria-hidden className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg border text-sm font-extrabold transition ${doneSteps.has(i) ? 'border-herb-500 bg-herb-500 text-white' : 'border-brand-600/40 bg-brand-600/15 text-brand-700'}`}>
                        {doneSteps.has(i) ? <Check /> : stepNumber(recipe.instructions, i)}
                      </span>
                      <span className={`text-lg leading-relaxed ${doneSteps.has(i) ? 'line-through' : ''}`}>{stripStepNumber(line)}</span>
                    </button>
                  </li>
                ),
              )}
            </ol>
          </div>
        </section>
      </div>
    </article>
  )
}
