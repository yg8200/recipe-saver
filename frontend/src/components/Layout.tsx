import { Link, NavLink, Outlet } from 'react-router'
import ThemeToggle from './ThemeToggle'

// The frame shared by every page: header + the current page's content.
// <Outlet /> is where React Router renders the page that matches the URL.
export default function Layout() {
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-10 border-b border-brand-100 bg-cream/90 pt-[env(safe-area-inset-top)] backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8 lg:px-12">
          <Link to="/" className="flex items-center gap-2.5 whitespace-nowrap text-lg font-bold">
            <span aria-hidden className="grid size-9 place-items-center rounded-xl bg-brand-600 text-xl shadow-sm">🍲</span>
            שומר המתכונים
          </Link>

          <nav className="flex items-center gap-1 whitespace-nowrap text-sm font-medium">
            {/* NavLink knows whether it matches the current URL, so we can highlight it */}
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `hidden rounded-lg px-3 py-2 transition sm:block ${isActive ? 'bg-brand-50 text-brand-700' : 'text-ink/70 hover:bg-brand-50/60 hover:text-ink'}`
              }
            >
              המתכונים שלי
            </NavLink>
            <NavLink
              to="/add"
              className="rounded-lg bg-brand-600 px-4 py-2.5 text-white shadow-sm transition hover:bg-brand-hover hover:shadow"
            >
              + הוספת מתכון
            </NavLink>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-10 lg:px-12 lg:py-12">
        <Outlet />
      </main>

      <footer className="px-5 pt-4 pb-[calc(2rem+env(safe-area-inset-bottom))] text-center text-sm text-ink/40">
        שומר המתכונים · קישורים, סרטונים ותמונות הופכים למתכונים
      </footer>
    </div>
  )
}
