// The backend answers in English ({"error": "..."}). The whole UI is Hebrew, so we translate the
// messages it can produce here, in one place, instead of scattering Hebrew through the API layer.
// Patterns are checked in order; the first match wins.
const TRANSLATIONS: [RegExp, (m: RegExpMatchArray) => string][] = [
  [/A recipe with the title '(.+)' already exists/, (m) => `כבר יש מתכון בשם “${m[1]}”.`],
  [/A recipe with this title already exists/, () => 'כבר יש מתכון עם השם הזה.'],
  [/'title' is required|'title' must be a non-empty string/, () => 'נא לתת למתכון שם.'],
  [/'ingredients' is required|'ingredients' must be a non-empty list/, () => 'נא להוסיף לפחות מצרך אחד.'],
  [/'instructions' is required|'instructions' must be a non-empty list/, () => 'נא להוסיף לפחות שלב אחד.'],
  [/must be a non-negative integer/, () => 'זמנים ומספר מנות חייבים להיות מספרים שלמים.'],
  [/'url' field is required/, () => 'נא להדביק קישור.'],
  [/Failed to fetch recipe webpage/, () => 'לא הצלחנו לפתוח את הדף. בדקו שהקישור תקין ושהאתר זמין.'],
  [/Could not extract readable text/, () => 'לא נמצא בדף טקסט שאפשר לקרוא.'],
  [/Invalid YouTube URL/, () => 'קישור היוטיוב אינו תקין.'],
  [/transcript is unavailable|Could not retrieve the video transcript/, () => 'לא נמצא מתכון בתיאור הסרטון, ואין לו תמלול זמין.'],
  [/Could not find a complete recipe/, () => 'לא הצלחנו למצוא מתכון מלא בסרטון.'],
  [/No ingredients were found/, () => 'לא נמצאו מצרכים במקור הזה.'],
  [/No instructions were found/, () => 'לא נמצאו הוראות הכנה במקור הזה.'],
  [/valid recipe title|did not return a valid JSON/, () => 'לא הצלחנו לזהות כאן מתכון.'],
  [/No image file provided|Empty file name/, () => 'לא נבחרה תמונה.'],
  [/too large/, () => 'התמונה גדולה מדי (עד 16MB).'],
  [/not a valid or supported image/, () => 'הקובץ אינו תמונה תקינה. נסו JPEG, PNG או HEIC.'],
  [/Recipe with id \d+ not found/, () => 'המתכון לא נמצא.'],
  [/Request body must be a valid JSON/, () => 'הבקשה אינה תקינה.'],
]

export function translateError(status: number, message: string): string {
  for (const [pattern, toHebrew] of TRANSLATIONS) {
    const match = message.match(pattern)
    if (match) return toHebrew(match)
  }
  // Unknown message (for example an unexpected server error): keep the original for developers
  // in the console and show a friendly Hebrew sentence to the user.
  console.error(`API error ${status}: ${message}`)
  if (status === 404) return 'לא נמצא.'
  if (status >= 500) return 'משהו השתבש בשרת. נסו שוב בעוד רגע.'
  return 'משהו השתבש. נסו שוב.'
}
