import { useMemo } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { useDeleteFolder, useFolders, useRenameFolder } from '../api/folders'
import { useRecipes } from '../api/recipes'
import FolderIcon from '../components/FolderIcon'
import RecipeCard from '../components/RecipeCard'
import { dangerButtonClass, inputClass, secondaryButtonClass } from '../components/RecipeForm'
import { EmptyState, ErrorMessage, Spinner } from '../components/StatusViews'
import NotFoundPage from './NotFoundPage'

// The inside of one folder: its name and the recipes that are in it.
export default function FolderPage() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const { data: folderList, isPending: foldersPending, error: foldersError, refetch: refetchFolders } = useFolders()
  const { data: recipeList, isPending: recipesPending, error: recipesError, refetch: refetchRecipes } = useRecipes()
  const renameFolder = useRenameFolder()
  const deleteFolder = useDeleteFolder()

  // Same idea as the home page: the search text lives in the URL (?q=...)
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q') ?? ''
  // Before the early returns: hooks can't be called conditionally
  const inFolder = useMemo(
    () => (recipeList ?? []).filter((r) => r.folder_ids.includes(id)),
    [recipeList, id],
  )
  // Search only inside this folder: filter the folder's recipes, not all recipes
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return inFolder
    return inFolder.filter(
      (r) => r.title.toLowerCase().includes(q) || r.ingredients.some((i) => i.toLowerCase().includes(q)),
    )
  }, [inFolder, query])

  const loadError = foldersError ?? recipesError
  if (loadError) return <ErrorMessage error={loadError} onRetry={() => { refetchFolders(); refetchRecipes() }} />
  // Checking the data itself (not just isPending) also tells TypeScript it is defined below
  if (foldersPending || recipesPending || !folderList || !recipeList) return <Spinner />

  const folder = folderList.find((f) => f.id === id)
  if (!folder) return <NotFoundPage />

  function handleRename() {
    const name = window.prompt('שם חדש לתיקייה', folder!.name)?.trim()
    if (!name || name === folder!.name) return
    renameFolder.mutate({ id, name })
  }

  function handleDelete() {
    if (!window.confirm(`למחוק את התיקייה “${folder!.name}”? המתכונים שבתוכה יישארו.`)) return
    deleteFolder.mutate(id, { onSuccess: () => navigate('/') })
  }

  const failure = renameFolder.error ?? deleteFolder.error

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 rounded-3xl border border-brand-100 bg-surface p-6 shadow-lg sm:flex-row sm:items-center sm:justify-between sm:p-8">
        <div className="space-y-2">
          <Link to="/" className="text-sm font-bold text-ink/60 transition hover:text-brand-600">
            <span className="inline-block rtl:rotate-180">←</span> כל המתכונים
          </Link>
          <h1 dir="auto" className="flex items-center gap-3 font-display text-3xl font-extrabold leading-tight">
            <FolderIcon className="size-7 text-brand-600" /> {folder.name}
          </h1>
          <p className="text-ink/60">{inFolder.length === 1 ? 'מתכון אחד' : `${inFolder.length} מתכונים`}</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button onClick={handleRename} className={secondaryButtonClass}>שינוי שם</button>
          <button
            onClick={handleDelete}
            disabled={deleteFolder.isPending}
            className={dangerButtonClass}
          >
            מחיקה
          </button>
        </div>
      </div>

      {failure && <ErrorMessage error={failure} />}

      {inFolder.length > 0 && (
        <input
          type="search"
          dir="auto"
          value={query}
          onChange={(e) => setSearchParams(e.target.value ? { q: e.target.value } : {}, { replace: true })}
          placeholder="חיפוש בתיקייה לפי שם או מצרך…"
          aria-label="חיפוש בתיקייה"
          className={`${inputClass} sm:max-w-xs`}
        />
      )}

      {inFolder.length === 0 ? (
        <EmptyState title="התיקייה ריקה">פתחו מתכון ובחרו את התיקייה הזו כדי להוסיף אותו לכאן.</EmptyState>
      ) : filtered.length === 0 ? (
        <EmptyState title="לא נמצאו תוצאות">אין מתכון בתיקייה שמתאים ל־“{query}”.</EmptyState>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {filtered.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  )
}
