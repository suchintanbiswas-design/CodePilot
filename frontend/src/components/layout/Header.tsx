import { useLocation, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';
import { ROUTES } from '@/config/routes';
import { Sun, Moon, LogOut, User, Settings, Shield, Search } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { Avatar } from '../ui/Avatar';
import { NotificationPopover } from './NotificationPopover';

export function Header() {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getPageTitle = () => {
    if (pathname === ROUTES.DASHBOARD) return 'Dashboard';
    if (pathname === ROUTES.NEW_REVIEW) return 'New Review';
    if (pathname.startsWith('/reviews/')) return 'Review Details';
    if (pathname === ROUTES.HISTORY) return 'History';
    if (pathname === ROUTES.ANALYTICS) return 'Analytics';
    if (pathname === ROUTES.PROFILE) return 'Profile';
    if (pathname === ROUTES.SETTINGS) return 'Settings';
    if (pathname === ROUTES.ADMIN) return 'Admin Panel';
    return 'CodePilot';
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-[var(--color-text-primary)] min-w-[120px]">
          {getPageTitle()}
        </h1>
      </div>

      <div className="flex-1 max-w-xl px-8 hidden md:block">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)]" size={18} />
          <input
            type="text"
            placeholder="Search reviews, files, or issues..."
            className="w-full bg-[var(--color-surface-secondary)] border border-transparent rounded-[var(--radius-full)] pl-10 pr-4 py-2 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--color-primary-500)] focus:ring-1 focus:ring-[var(--color-primary-500)] transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)] transition-colors focus:outline-none"
          title="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        <NotificationPopover />

        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 rounded-full focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:ring-offset-2 focus:ring-offset-[var(--color-surface)]"
          >
            <Avatar fallback={user?.fullName?.substring(0, 2)} />
          </button>

          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg origin-top-right animate-in fade-in slide-in-from-top-2">
              <div className="px-4 py-3 border-b border-[var(--color-border)]">
                <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                  {user?.fullName}
                </p>
                <p className="text-xs text-[var(--color-text-secondary)] truncate">
                  {user?.email}
                </p>
              </div>
              
              <div className="py-1">
                <Link
                  to={ROUTES.PROFILE}
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)]"
                >
                  <User size={16} />
                  Profile
                </Link>
                <Link
                  to={ROUTES.SETTINGS}
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)]"
                >
                  <Settings size={16} />
                  Settings
                </Link>
                {user?.role === 'admin' && (
                  <Link
                    to={ROUTES.ADMIN}
                    onClick={() => setIsDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)]"
                  >
                    <Shield size={16} />
                    Admin Panel
                  </Link>
                )}
              </div>
              
              <div className="border-t border-[var(--color-border)] py-1">
                <button
                  onClick={() => {
                    setIsDropdownOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-[var(--color-error)] hover:bg-[var(--color-error)]/10"
                >
                  <LogOut size={16} />
                  Log out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
