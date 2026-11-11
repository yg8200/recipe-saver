import { Link, useNavigate, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { useDeleteRecipe, useRecipe } from '../api/recipes'
import FolderPicker from '../components/FolderPicker'
import { secondaryButtonClass } from '../components/RecipeForm'
import RecipeMeta from '../components/RecipeMeta'
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
  const navigate = useNavigate()

  if (isPending) return <Spinner />
  if (error instanceof ApiError && error.status === 404) return <NotFoundPage />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />

  function handleDelete(title: string) {
    if (!window.confirm(`למחוק את “${title}”? אי אפשר לבטל את הפעולה.`)) return
    deleteRecipe.mutate(id, { onSuccess: () => navigate('/') })
  }

  return (
    <article className="space-y-8 sm:space-y-10">
      <div className="flex flex-col gap-4 rounded-3xl border border-brand-100 bg-surface p-6 shadow-sm sm:flex-row sm:items-start sm:justify-between sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:gap-6">
          {recipe.image_url && (
            <img
              src={imageSrc(recipe.image_url)!}
              alt={recipe.title}
              className="aspect-[4/3] w-full rounded-2xl object-cover shadow-sm sm:w-64 sm:shrink-0"
            />
          )}
          <div className="space-y-3">
            <Link to="/" className="text-sm text-ink/60 hover:text-ink">
              <span className="inline-block rtl:rotate-180">←</span> כל המתכונים
            </Link>
            <h1 dir="auto" className="text-3xl font-bold leading-tight">{recipe.title}</h1>
            <RecipeMeta recipe={recipe} />
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          <Link to={`/recipes/${id}/edit`} className={secondaryButtonClass}>עריכה</Link>
          <button
            onClick={() => handleDelete(recipe.title)}
            disabled={deleteRecipe.isPending}
            className="rounded-xl border border-danger-line bg-surface px-5 py-2.5 pointer-coarse:py-3 font-medium text-danger transition hover:bg-danger-bg disabled:opacity-60"
          >
            {deleteRecipe.isPending ? 'מוחק…' : 'מחיקה'}
          </button>
        </div>
      </div>

      {deleteRecipe.error && <ErrorMessage error={deleteRecipe.error} />}

      <FolderPicker recipe={recipe} />

      <div className="grid gap-6 sm:gap-8 md:grid-cols-[1fr_2fr]">
        <section className="h-fit rounded-2xl border border-brand-100 bg-surface p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">מצרכים</h2>
          <ul className="space-y-2">
            {recipe.ingredients.map((line, i) =>
              headerText(line) !== null ? (
                <li key={i} className="pt-2 text-sm font-semibold text-herb-700">{headerText(line)}</li>
              ) : (
                <li key={i} dir="auto" className="flex gap-2">
                  <span className="mt-2 size-1.5 shrink-0 rounded-full bg-herb-500" />
                  {line}
                </li>
              ),
            )}
          </ul>
        </section>

        <section className="rounded-2xl border border-brand-100 bg-surface p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">אופן הכנה</h2>
          <ol className="space-y-4 leading-relaxed">
            {recipe.instructions.map((line, i) =>
              headerText(line) !== null ? (
                <li key={i} className="pt-2 font-semibold text-brand-700">{headerText(line)}</li>
              ) : (
                <li key={i} dir="auto" className="flex gap-3">
                  <span aria-hidden className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                    {stepNumber(recipe.instructions, i)}
                  </span>
                  <span>{stripStepNumber(line)}</span>
                </li>
              ),
            )}
          </ol>
        </section>
      </div>
    </article>
  )
}
