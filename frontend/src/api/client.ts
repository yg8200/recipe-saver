// fetch() wrapper: adds the /api prefix and turns {"error": ...} into an ApiError

import { translateError } from './errors'

export class ApiError extends Error {
  readonly status: number
  // Set when the link was already extracted: the id of the recipe that was saved from it
  readonly existingRecipeId?: number

  constructor(status: number, message: string, existingRecipeId?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.existingRecipeId = existingRecipeId
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, init)
  } catch {
    // fetch() only throws when the request never reached a server (backend down, no network)
    throw new ApiError(0, 'אין חיבור לשרת. בדקו שהשרת פועל ונסו שוב.')
  }

  // Our Flask API always answers in JSON; fall back to null if the body is empty or not JSON
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const message = body?.error ?? `Request failed with status ${response.status}`
    throw new ApiError(response.status, translateError(response.status, message), body?.existing_recipe_id)
  }
  return body as T
}

// Convenience helper for JSON bodies (POST/PATCH)
export function jsonBody(data: unknown): RequestInit {
  return {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }
}
