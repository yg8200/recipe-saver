import { useNavigate } from 'react-router'
import { useCreateFolder, useFolders } from '../api/folders'
import FolderTile, { NewFolderTile } from './FolderTile'
import { ErrorMessage } from './StatusViews'

// The "Folders" section on the home page: a grid of square tiles plus a "new folder" tile.
export default function FolderGrid() {
  const { data: folders = [], error } = useFolders()
  const createFolder = useCreateFolder()
  const navigate = useNavigate()

  function handleCreate() {
    const name = window.prompt('שם התיקייה החדשה (למשל: המנות של סבתא)')?.trim()
    if (!name) return
    // Open the new folder right away, so the user can see it and start filling it
    createFolder.mutate(name, { onSuccess: (folder) => navigate(`/folders/${folder.id}`) })
  }

  return (
    <section className="space-y-4" aria-labelledby="folders-heading">
      <h2 id="folders-heading" className="text-xl font-semibold">תיקיות</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-5 lg:grid-cols-4 2xl:grid-cols-6">
        {folders.map((folder) => (
          <FolderTile key={folder.id} folder={folder} />
        ))}
        <NewFolderTile onClick={handleCreate} disabled={createFolder.isPending} />
      </div>
      {(createFolder.error ?? error) && <ErrorMessage error={(createFolder.error ?? error)!} />}
    </section>
  )
}
