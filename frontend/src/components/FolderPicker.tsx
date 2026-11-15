import { useState } from 'react'
import FolderIcon from './FolderIcon'
import NewFolderForm from './NewFolderForm'
import { useCreateFolder, useFolders, useToggleRecipeInFolder } from '../api/folders'
import type { Recipe } from '../api/types'
import { chipClass } from '../utils/chipClass'
import { ErrorMessage } from './StatusViews'

// Lets the user tick which folders a recipe belongs to. Each chip toggles membership.
export default function FolderPicker({ recipe }: { recipe: Recipe }) {
  const { data: folders = [] } = useFolders()
  const toggle = useToggleRecipeInFolder()
  const createFolder = useCreateFolder()

  const [creating, setCreating] = useState(false)

  function handleCreate(name: string) {
    // Create the folder, then put this recipe straight into it
    createFolder.mutate(name, {
      onSuccess: (folder) => {
        toggle.mutate({ folderId: folder.id, recipeId: recipe.id, inFolder: false })
        setCreating(false)
      },
    })
  }

  const failure = toggle.error ?? createFolder.error

  return (
    <section className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-brand-100 bg-surface px-5 py-4">
      <h2 className="text-xs font-bold text-ink/60">שיוך לתיקיות:</h2>
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
              <FolderIcon className="me-1.5 inline size-3.5 align-[-2px]" />{inFolder && '✓ '}
              {folder.name}
            </button>
          )
        })}
        {creating ? (
          <NewFolderForm
            onSubmit={handleCreate}
            onCancel={() => setCreating(false)}
            pending={createFolder.isPending}
            className="flex flex-wrap items-center gap-2"
          />
        ) : (
        <button
          onClick={() => setCreating(true)}
          className="rounded-xl border border-dashed border-brand-200 px-3.5 py-1.5 pointer-coarse:py-2.5 text-xs font-semibold text-ink/60 transition hover:border-brand-600 hover:text-brand-600 disabled:opacity-60"
        >
          + תיקייה חדשה
        </button>
        )}
      </div>
      {folders.length === 0 && <p className="w-full text-sm text-ink/60">עוד אין תיקיות. צרו אחת כדי לארגן את המתכונים.</p>}
      {failure && <ErrorMessage error={failure} />}
    </section>
  )
}
