import { useState, type FormEvent, type ReactNode } from 'react'
import type { Recipe, RecipeInput } from '../api/types'

// The form keeps everything as strings (that's what <input> and <textarea> give us)
// and only converts to the API shape (arrays, numbers) on submit.
interface FormValues {
  title: string
  ingredients: string
  instructions: string
  prep_time_minutes: string
  cook_time_minutes: string
  servings: string
}

function toFormValues(recipe?: Recipe): FormValues {
  return {
    title: recipe?.title ?? '',
    ingredients: recipe?.ingredients.join('\n') ?? '',
    instructions: recipe?.instructions.join('\n') ?? '',
    prep_time_minutes: recipe?.prep_time_minutes?.toString() ?? '',
    cook_time_minutes: recipe?.cook_time_minutes?.toString() ?? '',
    servings: recipe?.servings?.toString() ?? '',
  }
}

const toLines = (text: string) => text.split('\n').map((line) => line.trim()).filter(Boolean)
const toNumber = (text: string) => (text.trim() === '' ? null : Number(text))

// Same rules the backend enforces. Checking here too gives instant feedback without a round trip;
// the backend check still matters because anyone can call the API directly.
function validate(values: FormValues): string | null {
  if (!values.title.trim()) return 'Please give the recipe a title.'
  if (toLines(values.ingredients).length === 0) return 'Add at least one ingredient.'
  if (toLines(values.instructions).length === 0) return 'Add at least one step.'
  for (const field of ['prep_time_minutes', 'cook_time_minutes', 'servings'] as const) {
    const n = toNumber(values[field])
    if (n !== null && (!Number.isInteger(n) || n < 0)) return 'Times and servings must be whole numbers.'
  }
  return null
}

interface Props {
  initialRecipe?: Recipe
  submitLabel: string
  isSubmitting: boolean
  serverError?: Error | null
  onSubmit: (input: RecipeInput) => void
  onCancel?: () => void
}

export default function RecipeForm({ initialRecipe, submitLabel, isSubmitting, serverError, onSubmit, onCancel }: Props) {
  const [values, setValues] = useState(() => toFormValues(initialRecipe))
  const [validationError, setValidationError] = useState<string | null>(null)

  // A handler factory: update('title') returns the onChange function for the title field.
  // "...prev" copies the other fields, so only the one being typed in changes.
  const update = (field: keyof FormValues) => (e: { target: { value: string } }) =>
    setValues((prev) => ({ ...prev, [field]: e.target.value }))

  function handleSubmit(e: FormEvent) {
    e.preventDefault() // stop the browser's default full-page form submission
    const error = validate(values)
    setValidationError(error)
    if (error) return

    onSubmit({
      title: values.title.trim(),
      ingredients: toLines(values.ingredients),
      instructions: toLines(values.instructions),
      prep_time_minutes: toNumber(values.prep_time_minutes),
      cook_time_minutes: toNumber(values.cook_time_minutes),
      servings: toNumber(values.servings),
    })
  }

  const errorMessage = validationError ?? serverError?.message

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Field label="Title">
        <input dir="auto" value={values.title} onChange={update('title')} className={inputClass} placeholder="Classic Shakshuka" />
      </Field>

      <div className="grid gap-5 md:grid-cols-2">
        <Field label="Ingredients" hint="One per line">
          <textarea dir="auto" rows={10} value={values.ingredients} onChange={update('ingredients')} className={inputClass}
            placeholder={'4 eggs\n4 ripe tomatoes\n1 tsp cumin'} />
        </Field>
        <Field label="Steps" hint="One per line">
          <textarea dir="auto" rows={10} value={values.instructions} onChange={update('instructions')} className={inputClass}
            placeholder={'1. Sauté the peppers.\n2. Add tomatoes and simmer.'} />
        </Field>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Field label="Prep (min)">
          <input type="number" min={0} value={values.prep_time_minutes} onChange={update('prep_time_minutes')} className={inputClass} />
        </Field>
        <Field label="Cook (min)">
          <input type="number" min={0} value={values.cook_time_minutes} onChange={update('cook_time_minutes')} className={inputClass} />
        </Field>
        <Field label="Servings">
          <input type="number" min={0} value={values.servings} onChange={update('servings')} className={inputClass} />
        </Field>
      </div>

      {errorMessage && (
        <p role="alert" dir="auto" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800">{errorMessage}</p>
      )}

      <div className="flex gap-3">
        <button type="submit" disabled={isSubmitting} className={primaryButtonClass}>
          {isSubmitting ? 'Saving…' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className={secondaryButtonClass}>Cancel</button>
        )}
      </div>
    </form>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-baseline justify-between text-sm font-medium">
        {label}
        {hint && <span className="text-xs font-normal text-ink/50">{hint}</span>}
      </span>
      {children}
    </label>
  )
}

// Shared Tailwind class strings, exported so other pages style inputs/buttons the same way
export const inputClass =
  'w-full rounded-xl border border-brand-100 bg-white px-3.5 py-2.5 shadow-sm outline-none transition focus:border-brand-500 focus:ring-4 focus:ring-brand-100'
export const primaryButtonClass =
  'rounded-xl bg-brand-600 px-5 py-2.5 font-medium text-white shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60'
export const secondaryButtonClass =
  'rounded-xl border border-brand-100 bg-white px-5 py-2.5 font-medium transition hover:bg-brand-50'
