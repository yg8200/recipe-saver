import { createBrowserRouter } from 'react-router'
import Layout from './components/Layout'
import AddRecipePage from './pages/AddRecipePage'
import EditRecipePage from './pages/EditRecipePage'
import NotFoundPage from './pages/NotFoundPage'
import RecipeDetailPage from './pages/RecipeDetailPage'
import RecipeListPage from './pages/RecipeListPage'

// URL -> page. Every route is a child of Layout, so they all share the header;
// the matching child renders where Layout puts <Outlet />.
export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <RecipeListPage /> },
      { path: '/add', element: <AddRecipePage /> },
      { path: '/recipes/:id', element: <RecipeDetailPage /> },
      { path: '/recipes/:id/edit', element: <EditRecipePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
