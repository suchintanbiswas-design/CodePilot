import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/config/routes';
import { RegisterForm } from '@/components/auth/RegisterForm';

export function RegisterPage() {
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
        <h3 className="text-xl font-semibold text-[var(--color-text-primary)]">Create an account</h3>
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Get started with AI-powered code reviews</p>
      </div>
      <RegisterForm />
    </>
  );
}
