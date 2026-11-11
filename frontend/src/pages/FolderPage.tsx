import { Link, useNavigate, useParams } from 'react-router'
import { useDeleteFolder, useFolders, useRenameFolder } from '../api/folders'
import { useRecipes } from '../api/recipes'
import RecipeCard from '../components/RecipeCard'
import { secondaryButtonClass } from '../components/RecipeForm'
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

  const loadError = foldersError ?? recipesError
  if (loadError) return <ErrorMessage error={loadError} onRetry={() => { refetchFolders(); refetchRecipes() }} />
  // Checking the data itself (not just isPending) also tells TypeScript it is defined below
  if (foldersPending || recipesPending || !folderList || !recipeList) return <Spinner />

  const folder = folderList.find((f) => f.id === id)
  if (!folder) return <NotFoundPage />

  // The folder->recipes link lives on each recipe (folder_ids), so we just filter the cached list
  const inFolder = recipeList.filter((r) => r.folder_ids.includes(id))

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
      <div className="flex flex-col gap-4 rounded-3xl border border-brand-100 bg-surface p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between sm:p-8">
        <div className="space-y-2">
          <Link to="/" className="text-sm text-ink/60 hover:text-ink">
            <span className="inline-block rtl:rotate-180">←</span> כל המתכונים
          </Link>
          <h1 dir="auto" className="flex items-center gap-3 text-3xl font-bold leading-tight">
            <span aria-hidden>📁</span> {folder.name}
          </h1>
          <p className="text-ink/60">{inFolder.length === 1 ? 'מתכון אחד' : `${inFolder.length} מתכונים`}</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button onClick={handleRename} className={secondaryButtonClass}>שינוי שם</button>
          <button
            onClick={handleDelete}
            disabled={deleteFolder.isPending}
            className="rounded-xl border border-danger-line bg-surface px-5 py-2.5 pointer-coarse:py-3 font-medium text-danger transition hover:bg-danger-bg disabled:opacity-60"
          >
            מחיקה
          </button>
        </div>
      </div>

      {failure && <ErrorMessage error={failure} />}

      {inFolder.length === 0 ? (
        <EmptyState title="התיקייה ריקה">פתחו מתכון ובחרו את התיקייה הזו כדי להוסיף אותו לכאן.</EmptyState>
      ) : (
        <div className="grid gap-5 sm:gap-6 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
          {inFolder.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  )
}
