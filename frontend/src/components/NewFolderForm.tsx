import { useState, type FormEvent } from 'react'
import { inputClass, primaryButtonClass } from './RecipeForm'

export default function NewFolderForm({
  onSubmit,
  onCancel,
  pending,
  className = '',
}: {
  onSubmit: (name: string) => void
  onCancel: () => void
  pending?: boolean
  className?: string
}) {
  const [name, setName] = useState('')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (trimmed) onSubmit(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className={className}>
      <input
        autoFocus
        dir="auto"
        value={name}
        maxLength={100}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => e.key === 'Escape' && onCancel()}
        placeholder="שם התיקייה"
        aria-label="שם התיקייה החדשה"
        className={inputClass}
      />
      <div className="flex gap-2">
        <button type="submit" disabled={!name.trim() || pending} className={`${primaryButtonClass} !px-4 !py-2 text-xs`}>
          יצירה
        </button>
        <button type="button" onClick={onCancel} className="rounded-xl px-3 py-2 text-xs font-semibold text-ink/60 hover:text-brand-600">
          ביטול
        </button>
      </div>
    </form>
  )
}
