import { useEffect, useState, type DragEvent } from 'react'
import { secondaryButtonClass } from './RecipeForm'

interface Props {
  /** Photo already saved on the server (shown until a new file is chosen) */
  savedSrc?: string | null
  /** Called with the file the user picked or dropped */
  onChoose: (file: File) => void
  /** Called when the user removes the photo. Hide the button by leaving it out. */
  onRemove?: () => void
  busy?: boolean
}

// Picker for the dish photo: shows the current/chosen picture and lets the user choose, replace or remove it.
export default function ImageField({ savedSrc = null, onChoose, onRemove, busy = false }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  // Release the temporary preview URL (browser memory) when it changes or the component goes away
  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  function choose(files: FileList | null) {
    const file = files?.[0]
    if (!file) return
    setFileName(file.name)
    // HEIC can't be previewed by most browsers, so only create a preview for other formats
    setPreviewUrl(/\.(heic|heif)$/i.test(file.name) ? null : URL.createObjectURL(file))
    onChoose(file)
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault() // otherwise the browser opens the dropped file itself
    setDragging(false)
    choose(e.dataTransfer.files)
  }

  function handleRemove() {
    setPreviewUrl(null) // forget the locally chosen file too, not just the saved photo
    setFileName(null)
    onRemove?.()
  }

  const shown = previewUrl ?? savedSrc
  const hasPhoto = Boolean(shown || fileName)

  return (
    <div className="space-y-3">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed p-5 text-center transition ${
          dragging ? 'border-brand-500 bg-brand-50' : 'border-brand-200 hover:bg-brand-50/50'
        }`}
      >
        <input
          type="file"
          accept="image/*,.heic,.heif"
          className="sr-only"
          disabled={busy}
          onChange={(e) => choose(e.target.files)}
        />
        {shown ? (
          <img src={shown} alt="תמונת המנה" className="max-h-56 w-full rounded-xl object-cover" />
        ) : (
          <span className="text-4xl" aria-hidden>🍽️</span>
        )}
        <span className="text-sm font-medium">
          {fileName && !shown ? fileName : hasPhoto ? 'החלפת תמונה' : (
            <>
              <span className="pointer-coarse:hidden">גררו לכאן תמונה של המנה, או לחצו לבחירה</span>
              <span className="hidden pointer-coarse:inline">הקישו כדי לצלם או לבחור תמונה</span>
            </>
          )}
        </span>
      </label>

      {onRemove && hasPhoto && (
        <button type="button" onClick={handleRemove} disabled={busy} className={`${secondaryButtonClass} text-sm`}>
          הסרת התמונה
        </button>
      )}
    </div>
  )
}
