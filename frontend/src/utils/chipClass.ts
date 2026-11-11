// Tailwind classes for a pill-shaped toggle button ("chip"), used by the folder bar and picker.
export const chipClass = (selected: boolean) =>
  `rounded-full border px-4 py-1.5 pointer-coarse:py-2.5 text-sm font-medium whitespace-nowrap transition ${
    selected
      ? 'border-brand-600 bg-brand-600 text-white'
      : 'border-brand-100 bg-surface text-ink/80 hover:bg-brand-50'
  }`
