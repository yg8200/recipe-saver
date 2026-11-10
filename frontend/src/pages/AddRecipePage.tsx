import { useEffect, useState, type DragEvent, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { useCreateRecipe, useExtractFromImage, useExtractFromUrl } from '../api/recipes'
import type { Recipe } from '../api/types'
import RecipeForm, { inputClass, primaryButtonClass } from '../components/RecipeForm'
import { ErrorMessage } from '../components/StatusViews'

const TABS = [
  { id: 'link', label: '🔗 From a link' },
  { id: 'photo', label: '📷 From a photo' },
  { id: 'manual', label: '✍️ Type it in' },
] as const
type TabId = (typeof TABS)[number]['id']

export default function AddRecipePage() {
  // Active tab lives in the URL (?tab=photo) so the back button and refresh keep it
  const [searchParams, setSearchParams] = useSearchParams()
  const tab: TabId = TABS.some((t) => t.id === searchParams.get('tab')) ? (searchParams.get('tab') as TabId) : 'link'

  const navigate = useNavigate()
  const openRecipe = (recipe: Recipe) => navigate(`/recipes/${recipe.id}`)

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Add a recipe</h1>
        <p className="mt-1 text-ink/60">Paste a link, snap a photo of a cookbook page, or type it yourself.</p>
      </div>

      <div role="tablist" className="flex gap-1 rounded-2xl bg-brand-50 p-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setSearchParams({ tab: t.id }, { replace: true })}
            className={`flex-1 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
              tab === t.id ? 'bg-surface text-brand-700 shadow-sm' : 'text-ink/60 hover:text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="rounded-2xl border border-brand-100 bg-surface p-6 shadow-sm">
        {tab === 'link' && <FromLink onSaved={openRecipe} />}
        {tab === 'photo' && <FromPhoto onSaved={openRecipe} />}
        {tab === 'manual' && <Manual onSaved={openRecipe} />}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

function isYouTube(url: string) {
  try {
    const host = new URL(url).hostname.replace(/^www\./, '')
    return ['youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be'].includes(host)
  } catch {
    return false // not a valid URL (yet) while the user is typing
  }
}

function FromLink({ onSaved }: { onSaved: (r: Recipe) => void }) {
  const [url, setUrl] = useState('')
  const extract = useExtractFromUrl()
  const youtube = isYouTube(url)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (url.trim()) extract.mutate(url.trim(), { onSuccess: onSaved })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <label className="block">
        <span className="mb-1.5 block text-sm font-medium">Recipe website or YouTube video</span>
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://…"
          disabled={extract.isPending}
          className={inputClass}
        />
      </label>

      {url && (
        <p className="text-sm text-ink/60">
          {youtube
            ? '▶️ YouTube video: the recipe is read from the description, and the transcript fills in anything missing.'
            : '🌐 Website: the page is read and the recipe is pulled out by AI.'}
        </p>
      )}

      {extract.isPending ? (
        <Working message={() => (youtube ? 'Reading the video…' : 'Reading the page…')} />
      ) : (
        <button type="submit" className={primaryButtonClass}>Extract recipe</button>
      )}

      {extract.error && <ErrorMessage error={extract.error} />}
    </form>
  )
}

// ---------------------------------------------------------------------------

function FromPhoto({ onSaved }: { onSaved: (r: Recipe) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const extract = useExtractFromImage()

  // Free the last preview URL when the user leaves this tab or page.
  // This effect syncs with an external system (the browser's blob memory), which is what effects are for.
  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  function choose(files: FileList | null) {
    const chosen = files?.[0]
    if (!chosen) return
    setFile(chosen)
    // A temporary local URL lets <img> show the file before it is uploaded. Created here, in the
    // event that picked the file, rather than in an effect reacting to `file` changing.
    // HEIC can't be previewed by most browsers, so for those we show the file name instead.
    setPreviewUrl(/\.(heic|heif)$/i.test(chosen.name) ? null : URL.createObjectURL(chosen))
    extract.reset() // clear an error from a previous attempt
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault() // otherwise the browser opens the dropped file itself
    setDragging(false)
    choose(e.dataTransfer.files)
  }


  return (
    <div className="space-y-4">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed p-8 text-center transition ${
          dragging ? 'border-brand-500 bg-brand-50' : 'border-brand-200 hover:bg-brand-50/50'
        }`}
      >
        <input
          type="file"
          accept="image/*,.heic,.heif"
          className="sr-only"
          disabled={extract.isPending}
          onChange={(e) => choose(e.target.files)}
        />
        {previewUrl ? (
          <img src={previewUrl} alt="Selected recipe" className="max-h-72 rounded-xl object-contain" />
        ) : (
          <span className="text-4xl" aria-hidden>📷</span>
        )}
        <span className="font-medium">{file ? file.name : 'Drop a photo here, or click to choose'}</span>
        <span className="text-sm text-ink/50">JPEG, PNG or iPhone HEIC — a printed recipe works best</span>
      </label>

      {extract.isPending ? (
        <Working
          // Estimated stages, based on backend timing (~8s reading the photo, then the typo check)
          message={(seconds) => (seconds < 9 ? 'Reading the text from your photo…' : 'Double-checking for typos…')}
        />
      ) : (
        <button
          disabled={!file}
          onClick={() => file && extract.mutate(file, { onSuccess: onSaved })}
          className={primaryButtonClass}
        >
          Extract recipe
        </button>
      )}

      {extract.error && <ErrorMessage error={extract.error} />}
    </div>
  )
}

// ---------------------------------------------------------------------------

function Manual({ onSaved }: { onSaved: (r: Recipe) => void }) {
  const create = useCreateRecipe()
  return (
    <RecipeForm
      submitLabel="Save recipe"
      isSubmitting={create.isPending}
      serverError={create.error}
      onSubmit={(input) => create.mutate(input, { onSuccess: onSaved })}
    />
  )
}

// ---------------------------------------------------------------------------

// Shown only while a request runs. Because it is mounted fresh for every request, its
// counter starts at 0 each time without any reset logic; the interval is cleared on unmount.
function Working({ message }: { message: (seconds: number) => string }) {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div role="status" className="flex items-center gap-3 rounded-xl bg-brand-50 px-4 py-3 text-brand-700">
      <span className="size-5 shrink-0 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      <span className="flex-1">{message(seconds)}</span>
      <span className="tabular-nums text-sm text-brand-700/70">{seconds}s</span>
    </div>
  )
}
