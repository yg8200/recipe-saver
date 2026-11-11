import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest, jsonBody } from './client'
import type { Recipe, RecipeInput, RecipeUpdate } from './types'

// ---------------------------------------------------------------------------
// Plain API functions: one per backend endpoint. They know nothing about React.
// ---------------------------------------------------------------------------

export const recipesApi = {
  list: () => apiRequest<Recipe[]>('/recipes'),

  get: (id: number) => apiRequest<Recipe>(`/recipes/${id}`),

  create: (input: RecipeInput) => apiRequest<Recipe>('/recipes', { method: 'POST', ...jsonBody(input) }),

  update: (id: number, input: RecipeUpdate) =>
    apiRequest<Recipe>(`/recipes/${id}`, { method: 'PATCH', ...jsonBody(input) }),

  remove: (id: number) => apiRequest<{ message: string }>(`/recipes/${id}`, { method: 'DELETE' }),

  // Dish photo: multipart upload like extractFromImage. Replaces any existing photo.
  uploadImage: (id: number, file: File) => {
    const form = new FormData()
    form.append('image', file)
    return apiRequest<Recipe>(`/recipes/${id}/image`, { method: 'POST', body: form })
  },

  removeImage: (id: number) => apiRequest<Recipe>(`/recipes/${id}/image`, { method: 'DELETE' }),

  // Website or YouTube link: the backend decides which extractor to use
  extractFromUrl: (url: string) =>
    apiRequest<Recipe>('/recipes/extract', { method: 'POST', ...jsonBody({ url }) }),

  // Photo upload uses multipart/form-data. We pass a FormData object and do NOT set
  // Content-Type ourselves: the browser adds it, including the required "boundary".
  extractFromImage: (file: File) => {
    const form = new FormData()
    form.append('image', file)
    return apiRequest<Recipe>('/recipes/upload', { method: 'POST', body: form })
  },
}

// ---------------------------------------------------------------------------
// React hooks built on TanStack Query.
//
// useQuery   = reading data. It caches results under a "query key", tracks loading/error
//              state, and refetches when needed. Two components asking for the same key
//              share one request.
// useMutation = changing data (create/update/delete). After a successful change we
//              "invalidate" the affected keys so any screen showing them refetches.
// ---------------------------------------------------------------------------

export const recipeKeys = {
  all: ['recipes'] as const,
  detail: (id: number) => ['recipes', id] as const,
}

export function useRecipes() {
  return useQuery({ queryKey: recipeKeys.all, queryFn: recipesApi.list })
}

export function useRecipe(id: number) {
  return useQuery({ queryKey: recipeKeys.detail(id), queryFn: () => recipesApi.get(id) })
}

// Every way of creating a recipe ends the same way: put the new recipe in the
// cache (so its page opens instantly) and mark the list as stale.
function useCreateMutation<TVariables>(mutationFn: (vars: TVariables) => Promise<Recipe>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (recipe) => {
      queryClient.setQueryData(recipeKeys.detail(recipe.id), recipe)
      queryClient.invalidateQueries({ queryKey: recipeKeys.all, exact: true })
    },
  })
}

export const useCreateRecipe = () => useCreateMutation(recipesApi.create)
export const useExtractFromUrl = () => useCreateMutation(recipesApi.extractFromUrl)
export const useExtractFromImage = () => useCreateMutation(recipesApi.extractFromImage)

export function useUpdateRecipe(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: RecipeUpdate) => recipesApi.update(id, input),
    onSuccess: (recipe) => {
      queryClient.setQueryData(recipeKeys.detail(id), recipe)
      queryClient.invalidateQueries({ queryKey: recipeKeys.all, exact: true })
    },
  })
}

// Both photo actions return the updated recipe, so we put it straight into the cache.
function usePhotoMutation<TVariables>(mutationFn: (vars: TVariables) => Promise<Recipe>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (recipe) => {
      queryClient.setQueryData(recipeKeys.detail(recipe.id), recipe)
      queryClient.invalidateQueries({ queryKey: recipeKeys.all, exact: true })
    },
  })
}

export const useUploadImage = () =>
  usePhotoMutation(({ id, file }: { id: number; file: File }) => recipesApi.uploadImage(id, file))
export const useRemoveImage = () => usePhotoMutation((id: number) => recipesApi.removeImage(id))

export function useDeleteRecipe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: recipesApi.remove,
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: recipeKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: recipeKeys.all, exact: true })
    },
  })
}
