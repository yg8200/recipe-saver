import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { useToggleRecipeInFolder } from '../api/folders'
import type { Folder } from '../api/types'
import { RECIPE_DRAG_TYPE } from '../utils/dragDrop'

const tileBase =
  'group relative flex aspect-square flex-col items-center justify-center gap-2 overflow-hidden rounded-2xl p-4 text-center transition duration-200'

// One folder as a square tile. The whole tile is a link that opens the folder page,
// and also a drop target: drop a recipe card on it to add that recipe to the folder.
export default function FolderTile({ folder }: { folder: Folder }) {
  const addRecipe = useToggleRecipeInFolder()
  const [dragOver, setDragOver] = useState(false)
  const [status, setStatus] = useState<'added' | 'error' | null>(null)
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => () => window.clearTimeout(timer.current), [])

  const isRecipeDrag = (e: React.DragEvent) => e.dataTransfer.types.includes(RECIPE_DRAG_TYPE)

  function flash(next: 'added' | 'error') {
    setStatus(next)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => setStatus(null), 1800)
  }

  function handleDrop(e: React.DragEvent) {
    if (!isRecipeDrag(e)) return
    e.preventDefault() // stop the browser from "navigating" to the dragged link
    setDragOver(false)
    const recipeId = Number(e.dataTransfer.getData(RECIPE_DRAG_TYPE))
    // inFolder:false = "add". The endpoint is idempotent, so dropping twice is harmless.
    addRecipe.mutate(
      { folderId: folder.id, recipeId, inFolder: false },
      { onSuccess: () => flash('added'), onError: () => flash('error') },
    )
  }

  return (
    <Link
      to={`/folders/${folder.id}`}
      // By default the browser rejects drops. preventDefault() in dragover is what allows one.
      onDragOver={(e) => {
        if (!isRecipeDrag(e)) return
        e.preventDefault()
        e.dataTransfer.dropEffect = 'copy'
        setDragOver(true)
      }}
      // Leaving to a child element (the icon, the text) also fires dragleave; ignore that case
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragOver(false)
      }}
      onDrop={handleDrop}
      className={`${tileBase} border shadow-sm hover:-translate-y-1 hover:shadow-lg hover:shadow-brand-200/40 ${
        dragOver
          ? 'scale-105 border-herb-500 bg-herb-50 ring-2 ring-herb-500'
          : 'border-brand-100 bg-surface hover:border-brand-200'
      }`}
    >
      <span aria-hidden className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-herb-500 to-herb-100 transition-all duration-200 group-hover:h-1.5" />
      <span aria-hidden className="text-5xl transition group-hover:scale-110 sm:text-6xl">📁</span>
      <span dir="auto" className="line-clamp-2 text-base font-semibold leading-snug group-hover:text-brand-700">
        {folder.name}
      </span>
      <span role="status" className={`text-sm ${status === 'error' ? 'text-danger' : status ? 'font-medium text-herb-700' : 'text-ink/60'}`}>
        {status === 'added'
          ? '✓ המתכון נוסף'
          : status === 'error'
            ? 'ההוספה נכשלה'
            : folder.recipe_count === 1
              ? 'מתכון אחד'
              : `${folder.recipe_count} מתכונים`}
      </span>
    </Link>
  )
}

// The last tile of the grid: a dashed square that creates a new folder.
export function NewFolderTile({ onClick, disabled }: { onClick: () => void; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${tileBase} border-2 border-dashed border-brand-200 text-brand-700 hover:bg-brand-50 disabled:opacity-60`}
    >
      <span aria-hidden className="text-4xl">+</span>
      <span className="font-medium">תיקייה חדשה</span>
    </button>
  )
}
