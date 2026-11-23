import { useState } from 'react'

// Forget ticks a while after the last change, so next week starts clean
const EXPIRES_AFTER_MS = 6 * 60 * 60 * 1000

const onlyNumbers = (value: unknown): Set<number> =>
  new Set(Array.isArray(value) ? value.filter((n): n is number => typeof n === 'number') : [])

// Format: { items: number[], savedAt: ms }. Storage may be blocked, so fall back to empty
function load(key: string): Set<number> {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(key) ?? 'null')
    if (Array.isArray(parsed)) return onlyNumbers(parsed) // older format without a timestamp: keep it
    if (parsed && typeof parsed === 'object') {
      const { items, savedAt } = parsed as { items?: unknown; savedAt?: unknown }
      if (typeof savedAt === 'number' && Date.now() - savedAt < EXPIRES_AFTER_MS) return onlyNumbers(items)
      localStorage.removeItem(key) // too old: forget it
    }
  } catch {
    // unreadable or blocked storage: start empty
  }
  return new Set()
}

export function clearStoredSet(key: string) {
  try {
    localStorage.removeItem(key)
  } catch {
    // nothing to clean up if storage is unavailable
  }
}

// useState<Set<number>> that is also saved in localStorage under `key`
export function useStoredSet(key: string): [Set<number>, (next: Set<number>) => void] {
  const [state, setState] = useState(() => ({ key, set: load(key) }))

  // If the key changes (another recipe opened in the same page), load that recipe's saved set
  let current = state
  if (state.key !== key) {
    current = { key, set: load(key) }
    setState(current)
  }

  function update(next: Set<number>) {
    setState({ key, set: next })
    try {
      if (next.size === 0) localStorage.removeItem(key)
      else localStorage.setItem(key, JSON.stringify({ items: [...next], savedAt: Date.now() }))
    } catch {
      // Saving is best effort: the ticks still work for this visit
    }
  }

  return [current.set, update]
}
