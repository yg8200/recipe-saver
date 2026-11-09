import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useRecipes } from '../api/recipes'
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

  if (isPending) return <Spinner label="Loading your recipes…" />
  if (error) return <ErrorMessage error={error} onRetry={() => refetch()} />

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">My recipes</h1>
          <p className="mt-1 text-ink/60">
            {recipes.length} {recipes.length === 1 ? 'recipe' : 'recipes'} saved
          </p>
        </div>
        {recipes.length > 0 && (
          <input
            type="search"
            dir="auto"
            value={query}
            onChange={(e) => setSearchParams(e.target.value ? { q: e.target.value } : {}, { replace: true })}
            placeholder="Search by title or ingredient…"
            className={`${inputClass} sm:max-w-xs`}
          />
        )}
      </div>

      {recipes.length === 0 ? (
        <EmptyState title="No recipes yet">
          Save your first one from a website, a YouTube video or a photo.
          <div className="mt-4">
            <Link to="/add" className="font-medium text-brand-700 underline">Add a recipe</Link>
          </div>
        </EmptyState>
      ) : filtered.length === 0 ? (
        <EmptyState title="No matches">Nothing matches “{query}”.</EmptyState>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  )
}
