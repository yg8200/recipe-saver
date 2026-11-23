import { createBrowserRouter } from 'react-router'
import Layout from './components/Layout'
import AddRecipePage from './pages/AddRecipePage'
import EditRecipePage from './pages/EditRecipePage'
import FolderPage from './pages/FolderPage'
import NotFoundPage from './pages/NotFoundPage'
import RecipeDetailPage from './pages/RecipeDetailPage'
import RecipeListPage from './pages/RecipeListPage'

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <RecipeListPage /> },
      { path: '/add', element: <AddRecipePage /> },
      { path: '/recipes/:id', element: <RecipeDetailPage /> },
      { path: '/folders/:id', element: <FolderPage /> },
      { path: '/recipes/:id/edit', element: <EditRecipePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
