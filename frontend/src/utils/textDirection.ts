// Hebrew (U+0590–U+05FF) and Arabic (U+0600–U+06FF) characters are written right-to-left
const RTL_CHARS = /[֐-׿؀-ۿ]/

// Decide the layout direction for a whole recipe from its title. Setting dir="rtl" on a
// container mirrors everything inside it (text alignment, flex/grid order, list bullets),
// so a Hebrew recipe reads naturally instead of having Hebrew text in a left-to-right layout.
export function textDirection(text: string): 'rtl' | 'ltr' {
  return RTL_CHARS.test(text) ? 'rtl' : 'ltr'
}
