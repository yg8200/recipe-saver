import { useCreateFolder, useFolders, useToggleRecipeInFolder } from '../api/folders'
import type { Recipe } from '../api/types'
import { chipClass } from '../utils/chipClass'
import { ErrorMessage } from './StatusViews'

// Lets the user tick which folders a recipe belongs to. Each chip toggles membership.
export default function FolderPicker({ recipe }: { recipe: Recipe }) {
  const { data: folders = [] } = useFolders()
  const toggle = useToggleRecipeInFolder()
  const createFolder = useCreateFolder()

  function handleCreate() {
    const name = window.prompt('שם התיקייה החדשה')?.trim()
    if (!name) return
    // Create the folder, then put this recipe straight into it
    createFolder.mutate(name, {
      onSuccess: (folder) => toggle.mutate({ folderId: folder.id, recipeId: recipe.id, inFolder: false }),
    })
  }

  const failure = toggle.error ?? createFolder.error

  return (
    <section className="space-y-3 rounded-2xl border border-brand-100 bg-surface p-6 shadow-sm">
      <h2 className="text-lg font-semibold">תיקיות</h2>
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="תיקיות של המתכון">
        {folders.map((folder) => {
          const inFolder = recipe.folder_ids.includes(folder.id)
          return (
            <button
              key={folder.id}
              dir="auto"
              aria-pressed={inFolder}
              disabled={toggle.isPending}
              onClick={() => toggle.mutate({ folderId: folder.id, recipeId: recipe.id, inFolder })}
              className={`${chipClass(inFolder)} disabled:opacity-60`}
            >
              {inFolder ? '✓ ' : '📁 '}
              {folder.name}
            </button>
          )
        })}
        <button
          onClick={handleCreate}
          disabled={createFolder.isPending}
          className="rounded-full border border-dashed border-brand-200 px-4 py-1.5 pointer-coarse:py-2.5 text-sm font-medium text-brand-700 transition hover:bg-brand-50 disabled:opacity-60"
        >
          + תיקייה חדשה
        </button>
      </div>
      {folders.length === 0 && <p className="text-sm text-ink/60">עוד אין תיקיות. צרו אחת כדי לארגן את המתכונים.</p>}
      {failure && <ErrorMessage error={failure} />}
    </section>
  )
}
