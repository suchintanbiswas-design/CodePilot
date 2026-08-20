import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/components/ui/Toast';
import { ROUTES } from '@/config/routes';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { User, Mail, Lock, ShieldCheck } from 'lucide-react';

export function RegisterForm() {
  const [formData, setFormData] = useState({
    fullName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();
  const { error, success } = useToast();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.id]: e.target.value }));
  };

  const getPasswordStrength = (pass: string) => {
    if (!pass) return 0;
    let strength = 0;
    if (pass.length >= 8) strength += 25;
    if (pass.match(/[A-Z]/)) strength += 25;
    if (pass.match(/[0-9]/)) strength += 25;
    if (pass.match(/[^A-Za-z0-9]/)) strength += 25;
    return strength;
  };

  const strength = getPasswordStrength(formData.password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      error('Validation Error', 'Passwords do not match.');
      return;
    }

    if (strength < 50) {
      error('Weak Password', 'Please choose a stronger password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        fullName: formData.fullName,
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      success('Registration Successful', 'Welcome to CodePilot!');
      navigate(ROUTES.DASHBOARD);
    } catch (err: any) {
      error('Registration Failed', err.response?.data?.message || 'Please try again later.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <Input
          id="fullName"
          label="Full Name"
          placeholder="John Doe"
          value={formData.fullName}
          onChange={handleChange}
          leftIcon={<User size={18} />}
          required
        />

        <Input
          id="username"
          label="Username"
          placeholder="johndoe"
          value={formData.username}
          onChange={handleChange}
          leftIcon={<ShieldCheck size={18} />}
          required
        />
        
        <Input
          id="email"
          type="email"
          label="Email Address"
          placeholder="you@example.com"
          value={formData.email}
          onChange={handleChange}
          leftIcon={<Mail size={18} />}
          required
        />
        
        <div>
          <Input
            id="password"
            type="password"
            label="Password"
            placeholder="••••••••"
            value={formData.password}
            onChange={handleChange}
            leftIcon={<Lock size={18} />}
            required
          />
          {formData.password && (
            <div className="mt-2 h-1.5 w-full bg-[var(--color-surface-secondary)] rounded-full overflow-hidden flex">
              <div
                className={`h-full transition-all duration-300 ${
                  strength < 50 ? 'bg-[var(--color-error)]' : strength < 75 ? 'bg-[var(--color-warning)]' : 'bg-[var(--color-success)]'
                }`}
                style={{ width: `${strength}%` }}
              />
            </div>
          )}
        </div>

        <Input
          id="confirmPassword"
          type="password"
          label="Confirm Password"
          placeholder="••••••••"
          value={formData.confirmPassword}
          onChange={handleChange}
          leftIcon={<Lock size={18} />}
          required
          error={formData.password && formData.confirmPassword && formData.password !== formData.confirmPassword ? "Passwords do not match" : undefined}
        />
      </div>

      <Button
        type="submit"
        className="w-full"
        isLoading={isSubmitting}
      >
        Create Account
      </Button>
      
      <p className="text-center text-sm text-[var(--color-text-secondary)] mt-4">
        Already have an account?{' '}
        <Link to={ROUTES.LOGIN} className="font-medium text-[var(--color-primary-600)] hover:text-[var(--color-primary-500)]">
          Sign in
        </Link>
      </p>
    </form>
  );
}
