import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'
import { ApiError } from './api/client'
import './index.css'
import { router } from './router'

// One cache for all server data in the app (see src/api/recipes.ts)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // data is considered fresh for 30s, so moving between pages doesn't refetch every time
      // Retry network hiccups, but not 4xx answers like 404: asking again won't change them
      retry: (failureCount, error) =>
        failureCount < 2 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
    },
  },
})

// Entry point: find <div id="root"> in index.html and render the app into it.
// The providers make the query cache and the router available to every component below them.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
