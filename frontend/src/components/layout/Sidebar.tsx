import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/config/routes';
import { useAuth } from '@/hooks/useAuth';
import {
  LayoutDashboard,
  PlusCircle,
  History,
  BarChart3,
  Star,
  Settings,
  ChevronLeft,
  ChevronRight,
  Code2
} from 'lucide-react';
import { Avatar } from '../ui/Avatar';

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user } = useAuth();

  const navItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: ROUTES.DASHBOARD },
    { label: 'New Review', icon: PlusCircle, path: ROUTES.NEW_REVIEW },
    { label: 'History', icon: History, path: ROUTES.HISTORY },
    { label: 'Analytics', icon: BarChart3, path: ROUTES.ANALYTICS },
    { label: 'Favorites', icon: Star, path: ROUTES.FAVORITES },
  ];

  return (
    <aside
      className={cn(
        'hidden md:flex flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-all duration-300 z-10',
        collapsed ? 'w-[68px]' : 'w-[260px]'
      )}
    >
      <div className="flex h-16 items-center px-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary-500)] text-white shrink-0">
            <Code2 size={20} />
          </div>
          {!collapsed && (
            <span className="font-semibold text-lg text-[var(--color-text-primary)] truncate">
              CodePilot
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 py-6 px-3 flex flex-col gap-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-colors group',
                isActive
                  ? 'bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-900)]/20 text-[var(--color-primary-600)] dark:text-[var(--color-primary-400)]'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)]'
              )
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={20} className="shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </div>

      <div className="p-3 border-t border-[var(--color-border)] flex flex-col gap-1">
        <NavLink
          to={ROUTES.SETTINGS}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-colors group',
              isActive
                ? 'bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)]'
                : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)]'
            )
          }
          title={collapsed ? 'Settings' : undefined}
        >
          <Settings size={20} className="shrink-0" />
          {!collapsed && <span>Settings</span>}
        </NavLink>

        <div className="flex items-center justify-between mt-2 px-3 py-2">
          <NavLink
            to={ROUTES.PROFILE}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity min-w-0"
          >
            <Avatar
              fallback={user?.fullName?.substring(0, 2) || 'CP'}
              size="sm"
            />
            {!collapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                  {user?.fullName || 'User'}
                </span>
                <span className="text-xs text-[var(--color-text-tertiary)] truncate">
                  {user?.role || 'user'}
                </span>
              </div>
            )}
          </NavLink>
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] shadow-sm focus:outline-none"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>
    </aside>
  );
}
