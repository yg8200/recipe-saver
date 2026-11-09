import { Link, NavLink, Outlet } from 'react-router'

// The frame shared by every page: header + the current page's content.
// <Outlet /> is where React Router renders the page that matches the URL.
export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-brand-100 bg-cream/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 whitespace-nowrap text-lg font-bold">
            <span aria-hidden className="text-2xl">🍲</span>
            Recipe Saver
          </Link>

          <nav className="flex items-center gap-1 whitespace-nowrap text-sm font-medium">
            {/* NavLink knows whether it matches the current URL, so we can highlight it */}
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `hidden rounded-lg px-3 py-2 transition sm:block ${isActive ? 'text-brand-700' : 'text-ink/70 hover:text-ink'}`
              }
            >
              My recipes
            </NavLink>
            <NavLink
              to="/add"
              className="rounded-lg bg-brand-600 px-3 py-2 text-white shadow-sm transition hover:bg-brand-700"
            >
              + Add recipe
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
