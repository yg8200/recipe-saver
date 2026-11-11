import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest, jsonBody } from './client'
import { recipeKeys } from './recipes'
import type { Folder, Recipe } from './types'

export const foldersApi = {
  list: () => apiRequest<Folder[]>('/folders'),

  create: (name: string) => apiRequest<Folder>('/folders', { method: 'POST', ...jsonBody({ name }) }),

  rename: (id: number, name: string) =>
    apiRequest<Folder>(`/folders/${id}`, { method: 'PATCH', ...jsonBody({ name }) }),

  // Deletes the folder only; the recipes inside it are kept
  remove: (id: number) => apiRequest<{ message: string }>(`/folders/${id}`, { method: 'DELETE' }),

  addRecipe: (folderId: number, recipeId: number) =>
    apiRequest<Recipe>(`/folders/${folderId}/recipes/${recipeId}`, { method: 'PUT' }),

  removeRecipe: (folderId: number, recipeId: number) =>
    apiRequest<Recipe>(`/folders/${folderId}/recipes/${recipeId}`, { method: 'DELETE' }),
}

export const folderKeys = { all: ['folders'] as const }

export function useFolders() {
  return useQuery({ queryKey: folderKeys.all, queryFn: foldersApi.list })
}

// A folder change affects two caches: the folder list (names, recipe counts) and the recipes
// (each recipe carries its folder_ids). Invalidating both keeps every screen consistent.
function useFolderMutation<TVariables, TResult>(mutationFn: (vars: TVariables) => Promise<TResult>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: folderKeys.all })
      queryClient.invalidateQueries({ queryKey: recipeKeys.all }) // no `exact`: includes recipe detail entries
    },
  })
}

export const useCreateFolder = () => useFolderMutation(foldersApi.create)
export const useRenameFolder = () =>
  useFolderMutation(({ id, name }: { id: number; name: string }) => foldersApi.rename(id, name))
export const useDeleteFolder = () => useFolderMutation(foldersApi.remove)
export const useToggleRecipeInFolder = () =>
  useFolderMutation(({ folderId, recipeId, inFolder }: { folderId: number; recipeId: number; inFolder: boolean }) =>
    inFolder ? foldersApi.removeRecipe(folderId, recipeId) : foldersApi.addRecipe(folderId, recipeId),
  )
