// Tailwind classes for a toggle button ("chip"), used by the folder bar and picker.
export const chipClass = (selected: boolean) =>
  `rounded-xl border px-3.5 py-1.5 pointer-coarse:py-2.5 text-xs font-bold whitespace-nowrap transition ${
    selected
      ? 'border-brand-600 bg-brand-600/20 text-brand-700'
      : 'border-brand-100 bg-brand-50 text-ink/70 hover:border-brand-600/50'
  }`
