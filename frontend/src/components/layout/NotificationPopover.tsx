import { useState, useEffect, useRef } from 'react';
import { Bell, Check, Info, ShieldAlert, XCircle, CheckCircle2 } from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';
import api from '@/config/api';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export function NotificationPopover() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications');
      if (res.data?.success) {
        setNotifications(res.data.data);
      }
    } catch (err) {
      console.error("Failed to fetch notifications", err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Optional: poll every 30s
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const markAsRead = async (id: string) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
    } catch (err) {
      console.error("Failed to mark notification as read", err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const getIcon = (type: string) => {
    if (type.includes('security')) return <ShieldAlert size={16} className="text-[var(--color-warning)]" />;
    if (type.includes('failed')) return <XCircle size={16} className="text-[var(--color-error)]" />;
    if (type.includes('completed')) return <CheckCircle2 size={16} className="text-[var(--color-success)]" />;
    return <Info size={16} className="text-[var(--color-primary-500)]" />;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) fetchNotifications();
        }}
        className="relative flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-secondary)] hover:text-[var(--color-text-primary)] transition-colors focus:outline-none"
        title="Notifications"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute right-2 top-2 flex h-2 w-2 rounded-full bg-[var(--color-error)]">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-error)] opacity-75"></span>
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg origin-top-right animate-in fade-in slide-in-from-top-2 z-50">
          <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between sticky top-0 bg-[var(--color-surface)] z-10">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Notifications</h3>
            {unreadCount > 0 && (
              <span className="text-xs bg-[var(--color-primary-100)] text-[var(--color-primary-700)] dark:bg-[var(--color-primary-900)] dark:text-[var(--color-primary-300)] px-2 py-0.5 rounded-full font-medium">
                {unreadCount} new
              </span>
            )}
          </div>
          
          <div className="py-2">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-[var(--color-text-secondary)]">
                <Bell size={24} className="mx-auto mb-2 opacity-20" />
                No notifications yet
              </div>
            ) : (
              notifications.map(notif => (
                <div 
                  key={notif.id} 
                  className={`px-4 py-3 border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-secondary)] transition-colors flex gap-3 ${!notif.is_read ? 'bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-900)]/10' : ''}`}
                >
                  <div className="mt-0.5">
                    {getIcon(notif.type)}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[var(--color-text-primary)]">{notif.title}</p>
                    <p className="text-xs text-[var(--color-text-secondary)] mt-0.5">{notif.message}</p>
                    <p className="text-[10px] text-[var(--color-text-tertiary)] mt-1">
                      {formatRelativeTime(notif.created_at)}
                    </p>
                  </div>
                  {!notif.is_read && (
                    <button 
                      onClick={() => markAsRead(notif.id)}
                      className="text-[var(--color-text-tertiary)] hover:text-[var(--color-primary-500)] self-start mt-0.5"
                      title="Mark as read"
                    >
                      <Check size={14} />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
