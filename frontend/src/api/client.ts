// A thin wrapper around fetch() that every API call goes through.
// It adds the /api prefix (see the proxy in vite.config.ts) and turns
// the backend's {"error": "..."} responses into a typed ApiError.

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, init)
  } catch {
    // fetch() only throws when the request never reached a server (backend down, no network)
    throw new ApiError(0, 'Cannot reach the server. Is the backend running on port 5001?')
  }

  // Our Flask API always answers in JSON; fall back to null if the body is empty or not JSON
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const message = body?.error ?? `Request failed with status ${response.status}`
    throw new ApiError(response.status, message)
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
