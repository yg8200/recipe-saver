import { Link } from 'react-router'
import { EmptyState } from '../components/StatusViews'

export default function NotFoundPage() {
  return (
    <EmptyState title="Page not found">
      This recipe or page doesn't exist.
      <div className="mt-4">
        <Link to="/" className="font-medium text-brand-700 underline">Back to my recipes</Link>
      </div>
    </EmptyState>
  )
}
