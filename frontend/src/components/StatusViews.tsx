import type { ReactNode } from 'react'

// Small building blocks for the three states every data screen has: loading, error, empty.

export function Spinner({ label = 'טוען…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-16 text-ink/60">
      <span className="size-5 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      {label}
    </div>
  )
}

export function ErrorMessage({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-danger-line bg-danger-bg p-4 text-danger">
      <p dir="auto">{error.message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-2 text-sm font-medium underline">
          נסו שוב
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-2xl border-2 border-dashed border-brand-100 px-6 py-16 text-center">
      <p className="text-4xl" aria-hidden>🥄</p>
      <h2 className="mt-3 text-lg font-semibold">{title}</h2>
      <div className="mt-2 text-ink/60">{children}</div>
    </div>
  )
}
