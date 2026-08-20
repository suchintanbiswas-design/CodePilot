import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/config/routes';
import { LoginForm } from '@/components/auth/LoginForm';

export function LoginPage() {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated && !loading) {
      navigate(ROUTES.DASHBOARD, { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  return (
    <>
      <div className="mb-6 text-center">
        <h3 className="text-xl font-semibold text-[var(--color-text-primary)]">Sign in to your account</h3>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Enter your details to access your dashboard</p>
      </div>
      <LoginForm />
    </>
  );
}
