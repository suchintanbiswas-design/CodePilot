import { Button } from '@/components/ui/Button';
import { WifiOff, RefreshCw } from 'lucide-react';

export function NetworkErrorPage() {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-error)]/10 text-[var(--color-error)] mb-6">
        <WifiOff size={40} />
      </div>
      <h2 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-4">Connection Lost</h2>
      <p className="text-[var(--color-text-secondary)] max-w-md mb-8">
        Check your internet connection and try again.
      </p>
      <Button variant="primary" size="lg" onClick={() => window.location.reload()}>
        <RefreshCw className="mr-2" size={18} />
        Retry
      </Button>
    </div>
  );
}
