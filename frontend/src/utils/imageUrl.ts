// The API returns the photo's path ("/images/<name>.jpg"). In the browser every API path
// lives under /api (see the Vite/nginx proxy), so the <img> needs that prefix.
export const imageSrc = (imageUrl: string | null): string | null => (imageUrl ? `/api${imageUrl}` : null)
