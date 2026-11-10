import { useNavigate, useParams } from 'react-router'
import { useRecipe, useRemoveImage, useUpdateRecipe, useUploadImage } from '../api/recipes'
import ImageField from '../components/ImageField'
import RecipeForm from '../components/RecipeForm'
import { ErrorMessage, Spinner } from '../components/StatusViews'
import { imageSrc } from '../utils/imageUrl'

export default function EditRecipePage() {
  const id = Number(useParams().id)
  const { data: recipe, isPending, error } = useRecipe(id)
  const updateRecipe = useUpdateRecipe(id)
  const uploadImage = useUploadImage()
  const removeImage = useRemoveImage()
  const navigate = useNavigate()

  if (isPending) return <Spinner />
  if (error) return <ErrorMessage error={error} />

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <h1 className="text-3xl font-bold">עריכת מתכון</h1>

      {/* The photo is saved as soon as it is chosen, separately from the "save changes" button below */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium">תמונה של המנה</h2>
        <ImageField
          savedSrc={imageSrc(recipe.image_url)}
          busy={uploadImage.isPending || removeImage.isPending}
          onChoose={(file) => uploadImage.mutate({ id, file })}
          onRemove={recipe.image_url ? () => removeImage.mutate(id) : undefined}
        />
        {uploadImage.error && <ErrorMessage error={uploadImage.error} />}
        {removeImage.error && <ErrorMessage error={removeImage.error} />}
      </section>
      <RecipeForm
        initialRecipe={recipe}
        submitLabel="שמירת שינויים"
        isSubmitting={updateRecipe.isPending}
        serverError={updateRecipe.error}
        onSubmit={(input) => updateRecipe.mutate(input, { onSuccess: () => navigate(`/recipes/${id}`) })}
        onCancel={() => navigate(`/recipes/${id}`)}
      />
    </div>
  )
}
