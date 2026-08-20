import { Outlet } from 'react-router-dom';
import { Code2 } from 'lucide-react';

export function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-surface-secondary)] px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 animate-in fade-in zoom-in-95 duration-500">
        <div className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-primary-500)] text-white shadow-lg mb-4">
            <Code2 size={28} />
          </div>
          <h2 className="mt-2 text-center text-3xl font-bold tracking-tight text-[var(--color-text-primary)]">
            CodePilot
          </h2>
          <p className="mt-2 text-center text-sm text-[var(--color-text-secondary)]">
            AI-powered code review assistant
          </p>
        </div>
        
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
