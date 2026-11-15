import { useTheme } from '../utils/theme'

// Light/dark switch shown in the header (sun in dark mode, moon in light mode).
export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggle}
      role="switch"
      aria-checked={isDark}
      aria-label="מצב כהה"
      title={isDark ? 'מעבר למצב בהיר' : 'מעבר למצב כהה'}
      className="grid size-10 place-items-center rounded-xl border border-brand-100 bg-surface transition hover:border-brand-600 pointer-coarse:size-11"
    >
      {isDark ? (
        <svg aria-hidden viewBox="0 0 24 24" className="size-4 text-amber-400" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      ) : (
        <svg aria-hidden viewBox="0 0 24 24" className="size-4 text-ink/60" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      )}
    </button>
  )
}
