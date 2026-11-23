import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest, jsonBody } from './client'
import type { Recipe, RecipeInput, RecipeUpdate } from './types'

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

  // Don't set Content-Type: the browser adds it with the multipart boundary
  extractFromImage: (file: File) => {
    const form = new FormData()
    form.append('image', file)
    return apiRequest<Recipe>('/recipes/upload', { method: 'POST', body: form })
  },
}

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

// Seed the new recipe's cache entry so its page opens instantly
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
