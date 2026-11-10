import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'
const STORAGE_KEY = 'theme'

// localStorage can throw (private mode, blocked cookies), so every access is guarded.
function readStored(): Theme | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

const systemPrefersDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches

// The theme is just a class on <html>. index.html applies it before React loads (no white flash),
// so here we read what is already set instead of deciding again.
const currentTheme = (): Theme => (document.documentElement.classList.contains('dark') ? 'dark' : 'light')

function apply(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(currentTheme)

  // Until the user picks a theme themselves, follow the operating system's setting live.
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => {
      if (readStored()) return
      const next = systemPrefersDark() ? 'dark' : 'light'
      apply(next)
      setTheme(next)
    }
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  function toggle() {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    apply(next)
    setTheme(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      /* the choice still applies for this visit */
    }
  }

  return { theme, toggle }
}
