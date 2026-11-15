import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useCreateFolder, useFolders } from '../api/folders'
import FolderTile, { NewFolderTile } from './FolderTile'
import NewFolderForm from './NewFolderForm'
import { ErrorMessage } from './StatusViews'

// The "Folders" section on the home page: a grid of square tiles plus a "new folder" tile.
export default function FolderGrid() {
  const { data: folders = [], error } = useFolders()
  const createFolder = useCreateFolder()
  const navigate = useNavigate()

  const [creating, setCreating] = useState(false)

  function handleCreate(name: string) {
    // Open the new folder right away, so the user can see it and start filling it
    createFolder.mutate(name, { onSuccess: (folder) => navigate(`/folders/${folder.id}`) })
  }

  return (
    <section className="space-y-4" aria-labelledby="folders-heading">
      <div className="flex items-center justify-between">
        <h2 id="folders-heading" className="text-lg font-bold">תיקיות</h2>
        <span className="hidden text-xs text-ink/50 sm:inline">גררו מתכון על תיקייה כדי להוסיף אותו</span>
      </div>
      <div className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {folders.map((folder) => (
          <FolderTile key={folder.id} folder={folder} />
        ))}
        {creating ? (
          <NewFolderForm
            onSubmit={handleCreate}
            onCancel={() => setCreating(false)}
            pending={createFolder.isPending}
            className="col-span-2 flex flex-col justify-center gap-2 rounded-2xl border border-dashed border-brand-600 bg-surface/60 p-4 sm:col-span-1"
          />
        ) : (
          <NewFolderTile onClick={() => setCreating(true)} />
        )}
      </div>
      {(createFolder.error ?? error) && <ErrorMessage error={(createFolder.error ?? error)!} />}
    </section>
  )
}
