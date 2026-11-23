export const imageSrc = (imageUrl: string | null): string | null => (imageUrl ? `/api${imageUrl}` : null)
