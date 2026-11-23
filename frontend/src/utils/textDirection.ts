// Hebrew (U+0590–U+05FF) and Arabic (U+0600–U+06FF) characters are written right-to-left
const RTL_CHARS = /[֐-׿؀-ۿ]/

export function textDirection(text: string): 'rtl' | 'ltr' {
  return RTL_CHARS.test(text) ? 'rtl' : 'ltr'
}
