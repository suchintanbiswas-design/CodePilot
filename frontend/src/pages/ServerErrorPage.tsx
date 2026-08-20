import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/config/routes';
import { AlertTriangle, ArrowLeft, RefreshCw } from 'lucide-react';

interface ServerErrorPageProps {
  onRetry?: () => void;
}

export function ServerErrorPage({ onRetry }: ServerErrorPageProps = {}) {
  const navigate = useNavigate();
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-error)]/10 text-[var(--color-error)] mb-6">
        <AlertTriangle size={40} />
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] mb-2">500</h1>
      <h2 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-4">Something went wrong</h2>
      <p className="text-[var(--color-text-secondary)] max-w-md mb-8">
        We encountered an unexpected error on our servers. Please try again later.
      </p>
      <div className="flex gap-4">
        <Button variant="primary" size="lg" onClick={onRetry || (() => window.location.reload())}>
          <RefreshCw className="mr-2" size={18} />
          Try Again
        </Button>
        <Button variant="outline" size="lg" onClick={() => navigate(ROUTES.DASHBOARD)}>
          <ArrowLeft className="mr-2" size={18} />
          Back to Dashboard
        </Button>
      </div>
    </div>
  );
}
