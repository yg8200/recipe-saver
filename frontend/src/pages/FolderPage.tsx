import { useMemo } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { useDeleteFolder, useFolders, useRenameFolder } from '../api/folders'
import { useRecipes } from '../api/recipes'
import FolderIcon from '../components/FolderIcon'
import RecipeCard from '../components/RecipeCard'
import { inputClass, secondaryButtonClass } from '../components/RecipeForm'
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
  // The folder->recipes link lives on each recipe (folder_ids), so we just filter the cached list.
  // Hooks must run before the early returns below, hence useMemo up here.
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
      <div className="flex flex-col gap-4 rounded-xl border border-brand-100 bg-surface p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div className="space-y-2">
          <Link to="/" className="text-sm text-ink/60 hover:text-ink">
            <span className="inline-block rtl:rotate-180">←</span> כל המתכונים
          </Link>
          <h1 dir="auto" className="flex items-center gap-3 text-3xl font-semibold leading-tight">
            <FolderIcon className="size-7 text-brand-600" /> {folder.name}
          </h1>
          <p className="text-ink/60">{inFolder.length === 1 ? 'מתכון אחד' : `${inFolder.length} מתכונים`}</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button onClick={handleRename} className={secondaryButtonClass}>שינוי שם</button>
          <button
            onClick={handleDelete}
            disabled={deleteFolder.isPending}
            className="rounded-lg border border-danger-line bg-surface px-5 py-2.5 pointer-coarse:py-3 text-sm font-medium text-danger transition hover:bg-danger-bg disabled:opacity-60"
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
        <div className="grid gap-4 sm:gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
          {filtered.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  )
}
