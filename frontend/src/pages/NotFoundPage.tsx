import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/config/routes';
import { AlertCircle, ArrowLeft } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-error)]/10 text-[var(--color-error)] mb-6">
        <AlertCircle size={40} />
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] mb-2">404</h1>
      <h2 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-4">Page not found</h2>
      <p className="text-[var(--color-text-secondary)] max-w-md mb-8">
        Sorry, we couldn't find the page you're looking for. Perhaps you've mistyped the URL, or the page has been moved.
      </p>
      <Button variant="primary" size="lg" onClick={() => navigate(ROUTES.DASHBOARD)}>
        <ArrowLeft className="mr-2" size={18} />
        Back to Dashboard
      </Button>
    </div>
  );
}
