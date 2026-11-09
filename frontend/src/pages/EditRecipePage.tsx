import { useNavigate, useParams } from 'react-router'
import { useRecipe, useUpdateRecipe } from '../api/recipes'
import RecipeForm from '../components/RecipeForm'
import { ErrorMessage, Spinner } from '../components/StatusViews'

export default function EditRecipePage() {
  const id = Number(useParams().id)
  const { data: recipe, isPending, error } = useRecipe(id)
  const updateRecipe = useUpdateRecipe(id)
  const navigate = useNavigate()

  if (isPending) return <Spinner />
  if (error) return <ErrorMessage error={error} />

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold">Edit recipe</h1>
      <RecipeForm
        initialRecipe={recipe}
        submitLabel="Save changes"
        isSubmitting={updateRecipe.isPending}
        serverError={updateRecipe.error}
        onSubmit={(input) => updateRecipe.mutate(input, { onSuccess: () => navigate(`/recipes/${id}`) })}
        onCancel={() => navigate(`/recipes/${id}`)}
      />
    </div>
  )
}
