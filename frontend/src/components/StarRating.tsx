import { useState } from 'react'

const STARS = [1, 2, 3, 4, 5]

// A single star drawn as SVG: outline only when empty, filled when "on".
// currentColor lets the parent pick the color (text-star), so it follows the theme.
function Star({ filled, className }: { filled: boolean; className: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden className={className} fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={1.8} strokeLinejoin="round">
      <path d="M12 3.2l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17.2l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z" />
    </svg>
  )
}

interface Props {
  value: number | null
  // Omit onChange for a read-only display (used on the recipe cards)
  onChange?: (value: number | null) => void
  disabled?: boolean
}

export default function StarRating({ value, onChange, disabled }: Props) {
  // Which star the pointer is over: lights up the stars up to it as a preview before clicking
  const [hover, setHover] = useState<number | null>(null)
  const shown = hover ?? value ?? 0

  if (!onChange) {
    return (
      <span role="img" aria-label={value ? `דירוג ${value} מתוך 5` : 'אין דירוג'} className="flex gap-0.5 text-star">
        {STARS.map((n) => <Star key={n} filled={n <= (value ?? 0)} className="size-4" />)}
      </span>
    )
  }

  return (
    <div role="radiogroup" aria-label="דירוג" className="flex gap-1 text-star" onMouseLeave={() => setHover(null)}>
      {STARS.map((n) => (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={value === n}
          aria-label={n === 1 ? 'כוכב אחד' : `${n} כוכבים`}
          disabled={disabled}
          onMouseEnter={() => setHover(n)}
          // Clicking the star that is already selected clears the rating
          onClick={() => onChange(value === n ? null : n)}
          className="rounded p-0.5 pointer-coarse:p-1.5 transition hover:scale-110 disabled:opacity-60"
        >
          <Star filled={n <= shown} className="size-8 pointer-coarse:size-9" />
        </button>
      ))}
    </div>
  )
}
