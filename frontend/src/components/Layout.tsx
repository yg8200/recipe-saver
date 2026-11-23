import { Link, NavLink, Outlet } from 'react-router'
import { useRecipes } from '../api/recipes'
import ThemeToggle from './ThemeToggle'

// The frame shared by every page: header + the current page's content.
export default function Layout() {
  const { data: recipes } = useRecipes() // same cached request the home page uses
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-10 border-b border-brand-100 bg-cream/90 pt-[env(safe-area-inset-top)] backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3.5 sm:px-6 lg:px-8">
          <Link to="/" className="group flex items-center gap-3 whitespace-nowrap">
            <span aria-hidden className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-[#d95814] text-lg font-extrabold text-white shadow-lg shadow-brand-600/25 transition group-hover:scale-105">
              ש
            </span>
            <span className="text-lg font-extrabold tracking-tight sm:text-xl">שומר המתכונים</span>
            {recipes && (
              <span className="hidden rounded-full border border-brand-100 bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-ink/60 sm:inline-flex">
                {recipes.length} מתכונים
              </span>
            )}
          </Link>

          <nav className="flex items-center gap-2 whitespace-nowrap text-sm font-semibold sm:gap-3">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `hidden rounded-xl px-4 py-2 transition md:block ${isActive ? 'border border-brand-100 bg-brand-50' : 'text-ink/60 hover:text-ink'}`
              }
            >
              המתכונים שלי
            </NavLink>
            <NavLink
              to="/add"
              className="flex items-center gap-1.5 rounded-xl bg-gradient-to-l from-brand-600 to-brand-500 px-4 py-2.5 font-bold text-white shadow-md shadow-brand-600/25 transition hover:brightness-110"
            >
              <svg aria-hidden viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M12 5v14M5 12h14" />
              </svg>
              הוספת מתכון
            </NavLink>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
        <Outlet />
      </main>

      <footer className="px-5 pt-4 pb-[calc(2rem+env(safe-area-inset-bottom))] text-center text-xs text-ink/40">
        שומר המתכונים
      </footer>
    </div>
  )
}
