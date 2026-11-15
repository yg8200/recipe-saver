import { useEffect, useState, type DragEvent, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { ApiError } from '../api/client'
import { useCreateRecipe, useExtractFromImage, useExtractFromUrl, useUploadImage } from '../api/recipes'
import ImageField from '../components/ImageField'
import type { Recipe, RecipeInput } from '../api/types'
import RecipeForm, { inputClass, primaryButtonClass } from '../components/RecipeForm'
import { ErrorMessage } from '../components/StatusViews'

const TABS = [
  { id: 'link', label: 'מקישור' },
  { id: 'photo', label: 'מצילום' },
  { id: 'manual', label: 'הקלדה' },
] as const
type TabId = (typeof TABS)[number]['id']

export default function AddRecipePage() {
  // Active tab lives in the URL (?tab=photo) so the back button and refresh keep it
  const [searchParams, setSearchParams] = useSearchParams()
  const tab: TabId = TABS.some((t) => t.id === searchParams.get('tab')) ? (searchParams.get('tab') as TabId) : 'link'

  const navigate = useNavigate()
  const openRecipe = (recipe: Recipe) => navigate(`/recipes/${recipe.id}`)

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">הוספת מתכון</h1>
        <p className="mt-1 text-ink/60">הדביקו קישור, צלמו דף מספר בישול או הקלידו בעצמכם.</p>
      </div>

      <div role="tablist" className="flex gap-1 border-b border-brand-100">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setSearchParams({ tab: t.id }, { replace: true })}
            className={`-mb-px flex-1 border-b-2 px-3 py-2.5 text-sm font-medium transition sm:flex-none sm:px-5 ${
              tab === t.id ? 'border-brand-600 text-ink' : 'border-transparent text-ink/55 hover:text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-brand-100 bg-surface p-4 sm:p-6">
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

function isFacebook(url: string) {
  try {
    const host = new URL(url).hostname
    return host === 'fb.watch' || host === 'facebook.com' || host.endsWith('.facebook.com')
  } catch {
    return false
  }
}

function FromLink({ onSaved }: { onSaved: (r: Recipe) => void }) {
  const [url, setUrl] = useState('')
  const extract = useExtractFromUrl()
  const youtube = isYouTube(url)
  const facebook = isFacebook(url)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (url.trim()) extract.mutate(url.trim(), { onSuccess: onSaved })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <label className="block">
        <span className="mb-1.5 block text-sm font-medium">אתר מתכונים, סרטון יוטיוב או פוסט בפייסבוק</span>
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://…"
          dir="ltr"
          disabled={extract.isPending}
          className={inputClass}
        />
      </label>

      {url && (
        <p className="text-sm text-ink/60">
          {youtube
            ? 'סרטון יוטיוב: המתכון נקרא מתיאור הסרטון, והתמלול משלים את מה שחסר. תמונת הסרטון נשמרת כתמונת המנה.'
            : facebook
            ? 'פייסבוק: המתכון נקרא מטקסט הפוסט (חייב להיות כתוב שם), ותמונת הסרטון נשמרת כתמונת המנה. פוסטים פרטיים לא נתמכים.'
            : 'אתר: הדף נקרא והמתכון מחולץ באמצעות בינה מלאכותית. אם יש בדף תמונה של המנה, היא נשמרת גם.'}
        </p>
      )}

      {extract.isPending ? (
        <Working message={() => (youtube || facebook ? 'קוראים את הסרטון…' : 'קוראים את הדף…')} />
      ) : (
        <button type="submit" className={primaryButtonClass}>חילוץ מתכון</button>
      )}

      {extract.error && <ErrorMessage error={extract.error} />}
      {extract.error instanceof ApiError && extract.error.existingRecipeId && (
        <Link
          to={`/recipes/${extract.error.existingRecipeId}`}
          className="inline-block font-bold text-brand-700 underline"
        >
          לחצו כאן למעבר למתכון
        </Link>
      )}
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
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition ${
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
          <img src={previewUrl} alt="התמונה שנבחרה" className="max-h-72 rounded-xl object-contain" />
        ) : (
          <span className="text-4xl" aria-hidden>📷</span>
        )}
        <span className="font-medium">
          {file ? file.name : (
            <>
              <span className="pointer-coarse:hidden">גררו לכאן תמונה, או לחצו לבחירה</span>
              <span className="hidden pointer-coarse:inline">הקישו כדי לצלם או לבחור תמונה</span>
            </>
          )}
        </span>
        <span className="text-sm text-ink/50">JPEG, PNG או HEIC מאייפון. מתכון מודפס עובד הכי טוב</span>
      </label>

      {extract.isPending ? (
        <Working
          // Estimated stages, based on backend timing (~8s reading the photo, then the typo check)
          message={(seconds) => (seconds < 9 ? 'קוראים את הטקסט מהתמונה…' : 'בודקים שגיאות כתיב…')}
        />
      ) : (
        <button
          disabled={!file}
          onClick={() => file && extract.mutate(file, { onSuccess: onSaved })}
          className={primaryButtonClass}
        >
          חילוץ מתכון
        </button>
      )}

      {extract.error && <ErrorMessage error={extract.error} />}
    </div>
  )
}

// ---------------------------------------------------------------------------

function Manual({ onSaved }: { onSaved: (r: Recipe) => void }) {
  const create = useCreateRecipe()
  const uploadImage = useUploadImage()
  const [photo, setPhoto] = useState<File | null>(null)

  // Two requests: create the recipe, then attach the photo to it (the photo needs the new recipe's id).
  async function save(input: RecipeInput) {
    let recipe: Recipe
    try {
      recipe = await create.mutateAsync(input)
    } catch {
      return // the error is shown by the form through create.error
    }
    if (photo) {
      try {
        await uploadImage.mutateAsync({ id: recipe.id, file: photo })
      } catch {
        // The recipe is already saved; a failed photo shouldn't block it. It can be added from the edit page.
      }
    }
    onSaved(recipe)
  }

  return (
    <div className="space-y-5">
      <section className="space-y-2">
        <h2 className="text-sm font-medium">תמונה של המנה <span className="text-xs font-normal text-ink/50">אופציונלי</span></h2>
        <ImageField onChoose={setPhoto} onRemove={photo ? () => setPhoto(null) : undefined} />
      </section>
      <RecipeForm
        submitLabel="שמירת מתכון"
        isSubmitting={create.isPending || uploadImage.isPending}
        serverError={create.error}
        onSubmit={save}
      />
    </div>
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
      <span className="tabular-nums text-sm text-brand-700/70">{seconds} שנ׳</span>
    </div>
  )
}
