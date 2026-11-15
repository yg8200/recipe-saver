import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useRecipes } from '../api/recipes'
import FolderGrid from '../components/FolderGrid'
import RecipeCard from '../components/RecipeCard'
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
    <div className="space-y-9">
      <section className="relative overflow-hidden rounded-3xl border border-amber-200/15 bg-gradient-to-l from-[#d4621c] via-[#c25416] to-hero-to p-6 text-white shadow-xl shadow-black/20 sm:p-8">
        {/* Decorative circles, purely visual */}
        <span aria-hidden className="pointer-events-none absolute -start-10 -bottom-16 size-64 rounded-full bg-white/[0.07]" />
        <span aria-hidden className="pointer-events-none absolute start-36 -top-20 size-44 rounded-full bg-amber-300/[0.06]" />
        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
          <div className="space-y-1.5">
            <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">המתכונים שלי</h1>
            <p className="text-sm font-medium text-amber-100/90">
              {recipes.length === 1 ? 'מתכון אחד שמור' : `${recipes.length} מתכונים שמורים`} • מה מבשלים היום?
            </p>
          </div>
          {recipes.length > 0 && (
            <label className="relative block w-full lg:max-w-md">
              <svg aria-hidden viewBox="0 0 24 24" className="pointer-events-none absolute start-4 top-1/2 size-4 -translate-y-1/2 text-amber-200/70" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
              </svg>
              <input
                type="search"
                dir="auto"
                value={query}
                onChange={(e) => setSearchParams(e.target.value ? { q: e.target.value } : {}, { replace: true })}
                placeholder="חיפוש לפי שם מתכון או מצרך…"
                aria-label="חיפוש מתכונים"
                className="w-full rounded-2xl border border-amber-200/15 bg-[#16110e]/85 py-3.5 pe-4 ps-11 text-sm text-[#f7f1eb] shadow-inner outline-none backdrop-blur-md transition placeholder:text-amber-100/50 focus:border-amber-300/60"
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
          <div className="flex items-center gap-2.5">
            <h2 id="recipes-heading" className="text-lg font-bold">כל המתכונים</h2>
            <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-bold text-ink/60">{filtered.length}</span>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {filtered.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
