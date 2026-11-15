import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useRecipes } from '../api/recipes'
import FolderGrid from '../components/FolderGrid'
import RecipeCard from '../components/RecipeCard'
import { inputClass } from '../components/RecipeForm'
import { EmptyState, ErrorMessage, Spinner } from '../components/StatusViews'

export default function RecipeListPage() {
  const { data: recipes, isPending, error, refetch } = useRecipes()

  // The search text lives in the URL (?q=...) rather than in useState,
  // so a search survives a page refresh and can be shared as a link.
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q') ?? ''
  // useMemo: only re-filter when the recipes or the query change, not on every render
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!recipes || !q) return recipes ?? []
    return recipes.filter(
      (r) => r.title.toLowerCase().includes(q) || r.ingredients.some((i) => i.toLowerCase().includes(q)),
    )
  }, [recipes, query])

  if (isPending) return <Spinner label="טוענים את המתכונים…" />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />

  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-l from-hero-from to-hero-to p-6 text-white shadow-lg shadow-brand-500/20 sm:p-8">
        {/* Decorative circles, purely visual */}
        <span aria-hidden className="pointer-events-none absolute -start-10 -top-16 size-56 rounded-full bg-white/10" />
        <span aria-hidden className="pointer-events-none absolute -bottom-20 start-1/3 size-48 rounded-full bg-white/10" />
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold sm:text-4xl">המתכונים שלי</h1>
            <p className="mt-1 text-white/85">
              {recipes.length === 1 ? 'מתכון אחד שמור' : `${recipes.length} מתכונים שמורים`} · מה מבשלים היום?
            </p>
          </div>
          {recipes.length > 0 && (
            <label className="relative block sm:w-80">
              <svg aria-hidden viewBox="0 0 24 24" className="pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-ink/50" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
              </svg>
              <input
                type="search"
                dir="auto"
                value={query}
                onChange={(e) => setSearchParams(e.target.value ? { q: e.target.value } : {}, { replace: true })}
                placeholder="חיפוש לפי שם או מצרך…"
                aria-label="חיפוש מתכונים"
                className={`${inputClass} border-transparent text-ink ps-9`}
              />
            </label>
          )}
        </div>
      </section>

      {recipes.length > 0 && <FolderGrid />}

      {recipes.length === 0 ? (
        <EmptyState title="ספר המתכונים שלך עדיין ריק">
          שמרו את המתכון הראשון מאתר, מסרטון יוטיוב או מצילום של המתכון של סבתא.
          <div className="mt-4">
            <Link to="/add" className="font-medium text-brand-700 underline">הוספת מתכון</Link>
          </div>
        </EmptyState>
      ) : filtered.length === 0 ? (
        <EmptyState title="לא נמצאו תוצאות">אין מתכון שמתאים ל־“{query}”.</EmptyState>
      ) : (
        <section className="space-y-4" aria-labelledby="recipes-heading">
          <h2 id="recipes-heading" className="text-lg font-semibold">כל המתכונים</h2>
          <div className="grid gap-4 sm:gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
            {filtered.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
