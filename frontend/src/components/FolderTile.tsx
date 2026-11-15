import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { useToggleRecipeInFolder } from '../api/folders'
import type { Folder } from '../api/types'
import { RECIPE_DRAG_TYPE } from '../utils/dragDrop'
import FolderIcon from './FolderIcon'

// Two tones, alternating by folder id: orange and green. (Full class names are written out
// so Tailwind can see them at build time.)
const TONES = [
  {
    tile: 'border-[#f3d1b8] bg-[#fdf1e8] hover:border-brand-600 dark:border-[#52301b] dark:bg-[#2a180d]',
    icon: 'text-brand-600',
  },
  {
    tile: 'border-herb-100 bg-herb-50 hover:border-herb-500',
    icon: 'text-herb-500 dark:text-herb-700',
  },
]

const tileBase = 'group relative flex flex-col items-center justify-center gap-0.5 overflow-hidden rounded-2xl p-5 text-center transition'

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
      className={`${tileBase} border ${
        dragOver
          ? 'border-brand-600 bg-brand-50 ring-2 ring-brand-600/50 scale-[1.02]'
          : `${tone.tile} hover:shadow-md`
      }`}
    >
      <span className={`mb-2 grid size-11 place-items-center rounded-2xl bg-white/80 transition group-hover:scale-110 dark:bg-black/25 ${tone.icon}`}>
        <FolderIcon className="size-5" />
      </span>
      <span dir="auto" className="line-clamp-2 text-sm font-bold leading-snug">
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
export function NewFolderTile({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`${tileBase} group border border-dashed border-brand-200 bg-surface/60 text-ink/60 hover:border-brand-600 hover:text-brand-600`}
    >
      <span aria-hidden className="mb-2 grid size-11 place-items-center rounded-2xl bg-brand-50 text-2xl leading-none transition">+</span>
      <span className="text-sm font-semibold">תיקייה חדשה</span>
      <span className="text-[11px] text-ink/45">ארגון לפי חג או קטגוריה</span>
    </button>
  )
}
