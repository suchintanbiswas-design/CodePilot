import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/components/ui/Toast';
import { ROUTES } from '@/config/routes';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Mail, Lock } from 'lucide-react';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const { error, success } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      error('Validation Error', 'Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email, password });
      success('Login Successful', 'Welcome back to CodePilot!');
      navigate(ROUTES.DASHBOARD);
    } catch (err: any) {
      error('Login Failed', err.response?.data?.message || 'Invalid email or password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <Input
          id="email"
          type="email"
          label="Email Address"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail size={18} />}
          required
        />
        
        <Input
          id="password"
          type="password"
          label="Password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock size={18} />}
          required
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            id="remember-me"
            name="remember-me"
            type="checkbox"
            className="h-4 w-4 rounded border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-primary-600)] focus:ring-[var(--color-primary-500)]"
          />
          <label htmlFor="remember-me" className="ml-2 block text-sm text-[var(--color-text-secondary)]">
            Remember me
          </label>
        </div>

        <div className="text-sm">
          <a href="#" className="font-medium text-[var(--color-primary-600)] hover:text-[var(--color-primary-500)]">
            Forgot password?
          </a>
        </div>
      </div>

      <Button
        type="submit"
        className="w-full"
        isLoading={isSubmitting}
      >
        Sign In
      </Button>
      
      <p className="text-center text-sm text-[var(--color-text-secondary)] mt-4">
        Don't have an account?{' '}
        <Link to={ROUTES.REGISTER} className="font-medium text-[var(--color-primary-600)] hover:text-[var(--color-primary-500)]">
          Sign up
        </Link>
      </p>
    </form>
  );
}
