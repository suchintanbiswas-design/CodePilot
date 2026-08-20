import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useTheme } from '@/hooks/useTheme';
import { Shield, Download, Trash2, Globe, Monitor, Moon, Sun, Code2 } from 'lucide-react';
import api from '@/config/api';
import { ROUTES } from '@/config/routes';

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  
  const [preferences, setPreferences] = useState({
    defaultLanguage: 'TypeScript',
    defaultMode: 'Strict'
  });

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // Fetch current preferences on load
  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const res = await api.get('/users/me/preferences');
        if (res.data?.data) {
          setPreferences(prev => ({ ...prev, ...res.data.data }));
        }
      } catch (err) {
        console.error("Failed to load preferences", err);
      }
    };
    fetchPreferences();
  }, []);

  const handleSavePreferences = async () => {
    try {
      await api.put('/users/me/preferences', preferences);
      alert('Preferences saved successfully');
    } catch (err) {
      console.error('Failed to save preferences', err);
      alert('Failed to save preferences');
    }
  };

  const handleUpdatePassword = async () => {
    setPasswordError('');
    setPasswordSuccess('');
    
    if (!passwordForm.currentPassword || !passwordForm.newPassword) {
      setPasswordError('Please fill in all fields');
      return;
    }
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }
    
    if (passwordForm.newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }
    
    try {
      await api.put('/users/me/password', {
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword
      });
      setPasswordSuccess('Password updated successfully');
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err: any) {
      setPasswordError(err.response?.data?.detail || 'Failed to update password');
    }
  };

  const handleExportData = async () => {
    try {
      const response = await api.get('/users/me/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'codepilot_export.json');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export data', err);
      alert('Failed to export data. Please try again.');
    }
  };

  const handleDeleteAccount = async () => {
    if (window.confirm('Are you sure you want to deactivate your account? You will be logged out immediately.')) {
      try {
        await api.delete('/users/me');
        // Clear token and redirect
        localStorage.removeItem('token');
        window.location.href = ROUTES.LOGIN;
      } catch (err) {
        console.error('Failed to delete account', err);
        alert('Failed to delete account. Please try again later.');
      }
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Settings</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">Manage your account preferences and configurations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] flex items-center gap-2 mb-2">
            <Monitor size={18} />
            Appearance
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)]">Customize how CodePilot looks on your device.</p>
        </div>
        
        <Card className="md:col-span-2 p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-3">Theme</label>
            <div className="grid grid-cols-3 gap-4">
              <button 
                onClick={() => setTheme('light')}
                className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all ${theme === 'light' ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-900)]/20' : 'border-[var(--color-border)] hover:border-[var(--color-text-tertiary)]'}`}
              >
                <Sun size={24} className="mb-2" />
                <span className="text-sm font-medium">Light</span>
              </button>
              <button 
                onClick={() => setTheme('dark')}
                className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all ${theme === 'dark' ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-900)]/20' : 'border-[var(--color-border)] hover:border-[var(--color-text-tertiary)]'}`}
              >
                <Moon size={24} className="mb-2" />
                <span className="text-sm font-medium">Dark</span>
              </button>
              <button 
                onClick={() => setTheme('system')}
                className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all ${theme === 'system' ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-900)]/20' : 'border-[var(--color-border)] hover:border-[var(--color-text-tertiary)]'}`}
              >
                <Monitor size={24} className="mb-2" />
                <span className="text-sm font-medium">System</span>
              </button>
            </div>
          </div>
        </Card>
      </div>

      <div className="h-px bg-[var(--color-border)] w-full my-8"></div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] flex items-center gap-2 mb-2">
            <Code2 size={18} />
            Review Preferences
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)]">Set your fallback settings for new code reviews.</p>
        </div>
        
        <Card className="md:col-span-2 p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">Fallback Language</label>
              <select 
                value={preferences.defaultLanguage}
                onChange={(e) => setPreferences({...preferences, defaultLanguage: e.target.value})}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)]"
              >
                <option>TypeScript</option>
                <option>JavaScript</option>
                <option>Python</option>
                <option>Go</option>
                <option>Rust</option>
                <option>Java</option>
              </select>
              <p className="text-xs text-[var(--color-text-secondary)] mt-1">Used only if auto-detection fails.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">Default Mode</label>
              <select 
                value={preferences.defaultMode}
                onChange={(e) => setPreferences({...preferences, defaultMode: e.target.value})}
                className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)]"
              >
                <option>Strict</option>
                <option>Standard</option>
                <option>Lenient</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end">
            <Button onClick={handleSavePreferences}>Save Preferences</Button>
          </div>
        </Card>
      </div>

      <div className="h-px bg-[var(--color-border)] w-full my-8"></div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] flex items-center gap-2 mb-2">
            <Shield size={18} />
            Security
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)]">Update your password and secure your account.</p>
        </div>
        
        <Card className="md:col-span-2 p-6 space-y-6">
          <div className="space-y-4">
            {passwordError && <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-200">{passwordError}</div>}
            {passwordSuccess && <div className="p-3 bg-green-50 text-green-600 text-sm rounded-lg border border-green-200">{passwordSuccess}</div>}
            
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">Current Password</label>
              <Input 
                type="password" 
                placeholder="••••••••" 
                value={passwordForm.currentPassword}
                onChange={e => setPasswordForm({...passwordForm, currentPassword: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">New Password</label>
              <Input 
                type="password" 
                placeholder="••••••••" 
                value={passwordForm.newPassword}
                onChange={e => setPasswordForm({...passwordForm, newPassword: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">Confirm New Password</label>
              <Input 
                type="password" 
                placeholder="••••••••" 
                value={passwordForm.confirmPassword}
                onChange={e => setPasswordForm({...passwordForm, confirmPassword: e.target.value})}
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button onClick={handleUpdatePassword}>Update Password</Button>
          </div>
        </Card>
      </div>

      <div className="h-px bg-[var(--color-border)] w-full my-8"></div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] flex items-center gap-2 mb-2">
            <Globe size={18} />
            Data & Privacy
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)]">Manage your data and account deletion.</p>
        </div>
        
        <Card className="md:col-span-2 p-6 space-y-6">
          <div className="flex items-start justify-between p-4 border border-[var(--color-border)] rounded-xl">
            <div>
              <h4 className="text-sm font-medium text-[var(--color-text-primary)] flex items-center gap-2">
                <Download size={16} className="text-[var(--color-primary-500)]" />
                Export Account Data
              </h4>
              <p className="text-xs text-[var(--color-text-secondary)] mt-1 max-w-sm">
                Download a JSON file containing all your settings, profile info, and review history.
              </p>
            </div>
            <Button variant="outline" onClick={handleExportData}>Export JSON</Button>
          </div>

          <div className="flex items-start justify-between p-4 border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/10 rounded-xl">
            <div>
              <h4 className="text-sm font-medium text-red-600 dark:text-red-400 flex items-center gap-2">
                <Trash2 size={16} />
                Deactivate Account
              </h4>
              <p className="text-xs text-red-500/80 dark:text-red-300/80 mt-1 max-w-sm">
                Deactivate your personal account. Your existing reviews and reports will be retained.
              </p>
            </div>
            <Button variant="outline" className="text-red-600 border-red-200 hover:bg-red-100 hover:text-red-700 dark:border-red-900 dark:hover:bg-red-900/50" onClick={handleDeleteAccount}>
              Deactivate Account
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
