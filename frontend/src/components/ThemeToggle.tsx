import { useTheme } from '../utils/theme'

// Light/dark switch shown in the header.
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
      className="grid size-9 place-items-center pointer-coarse:size-11 rounded-lg text-lg transition hover:bg-brand-50"
    >
      <span aria-hidden>{isDark ? '☀️' : '🌙'}</span>
    </button>
  )
}
