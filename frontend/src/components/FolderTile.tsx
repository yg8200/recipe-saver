import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { useToggleRecipeInFolder } from '../api/folders'
import type { Folder } from '../api/types'
import { RECIPE_DRAG_TYPE } from '../utils/dragDrop'
import FolderIcon from './FolderIcon'

// Each folder gets its own color, picked by its id, so the tiles are easy to tell apart.
// (Full class names are written out so Tailwind can see them at build time.)
const TONES = [
  { tile: 'bg-brand-50 border-brand-200', icon: 'text-brand-600' },
  { tile: 'bg-herb-50 border-herb-100', icon: 'text-herb-700' },
  { tile: 'bg-sky-100 border-sky-200 dark:bg-sky-950 dark:border-sky-900', icon: 'text-sky-600 dark:text-sky-300' },
  { tile: 'bg-violet-100 border-violet-200 dark:bg-violet-950 dark:border-violet-900', icon: 'text-violet-600 dark:text-violet-300' },
  { tile: 'bg-rose-100 border-rose-200 dark:bg-rose-950 dark:border-rose-900', icon: 'text-rose-600 dark:text-rose-300' },
  { tile: 'bg-amber-100 border-amber-200 dark:bg-amber-950 dark:border-amber-900', icon: 'text-amber-600 dark:text-amber-300' },
]

const tileBase =
  'group relative flex aspect-[4/3] flex-col items-center justify-center gap-1.5 overflow-hidden rounded-xl p-3 text-center transition'

// One folder as a square tile. The whole tile is a link that opens the folder page,
// and also a drop target: drop a recipe card on it to add that recipe to the folder.
export default function FolderTile({ folder }: { folder: Folder }) {
  const tone = TONES[folder.id % TONES.length]
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
      className={`${tileBase} border hover:border-brand-200 hover:shadow-md hover:shadow-black/5 ${
        dragOver
          ? 'border-brand-500 bg-brand-50 ring-2 ring-brand-500/40'
          : `${tone.tile} hover:shadow-md`
      }`}
    >
      <FolderIcon className={`size-9 ${tone.icon}`} />
      <span dir="auto" className="line-clamp-2 text-sm font-semibold leading-snug">
        {folder.name}
      </span>
      <span role="status" className={`text-xs ${status === 'error' ? 'text-danger' : status ? 'font-medium text-brand-700' : 'text-ink/55'}`}>
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
      className={`${tileBase} border border-dashed border-brand-200 text-ink/60 hover:text-ink hover:border-brand-500 disabled:opacity-60`}
    >
      <span aria-hidden className="text-2xl leading-none">+</span>
      <span className="text-sm font-medium">תיקייה חדשה</span>
    </button>
  )
}
