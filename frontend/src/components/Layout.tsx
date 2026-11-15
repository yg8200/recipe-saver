import { Link, NavLink, Outlet } from 'react-router'
import ThemeToggle from './ThemeToggle'

// The frame shared by every page: header + the current page's content.
// <Outlet /> is where React Router renders the page that matches the URL.
export default function Layout() {
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-10 border-b border-brand-100 bg-cream/90 pt-[env(safe-area-inset-top)] backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-8 lg:px-12">
          <Link to="/" className="flex items-center gap-2.5 whitespace-nowrap font-semibold tracking-tight">
            <span aria-hidden className="grid size-7 place-items-center rounded-md bg-brand-600 text-sm font-bold text-white">ש</span>
            שומר המתכונים
          </Link>

          <nav className="flex items-center gap-1 whitespace-nowrap text-sm font-medium">
            {/* NavLink knows whether it matches the current URL, so we can highlight it */}
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `hidden rounded-md px-3 py-1.5 transition sm:block ${isActive ? 'bg-brand-50 text-ink' : 'text-ink/60 hover:text-ink'}`
              }
            >
              המתכונים שלי
            </NavLink>
            <NavLink
              to="/add"
              className="rounded-lg bg-brand-600 px-3.5 py-2 text-white transition hover:bg-brand-hover"
            >
              הוספת מתכון
            </NavLink>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10 lg:px-12">
        <Outlet />
      </main>

      <footer className="px-5 pt-4 pb-[calc(2rem+env(safe-area-inset-bottom))] text-center text-xs text-ink/40">
        שומר המתכונים
      </footer>
    </div>
  )
}
