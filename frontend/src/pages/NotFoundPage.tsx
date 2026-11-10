import { Link } from 'react-router'
import { EmptyState } from '../components/StatusViews'

export default function NotFoundPage() {
  return (
    <EmptyState title="הדף לא נמצא">
      המתכון או הדף שחיפשתם לא קיימים.
      <div className="mt-4">
        <Link to="/" className="font-medium text-brand-700 underline">חזרה למתכונים שלי</Link>
      </div>
    </EmptyState>
  )
}
