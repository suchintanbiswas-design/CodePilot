import { createContext, useContext, useState, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  title: string;
  description?: string;
  type: ToastType;
}

interface ToastContextType {
  toast: (options: Omit<Toast, 'id'>) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
  warning: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toastMethods = {
    toast: addToast,
    success: (title: string, description?: string) => addToast({ title, description, type: 'success' }),
    error: (title: string, description?: string) => addToast({ title, description, type: 'error' }),
    info: (title: string, description?: string) => addToast({ title, description, type: 'info' }),
    warning: (title: string, description?: string) => addToast({ title, description, type: 'warning' }),
  };

  return (
    <ToastContext.Provider value={toastMethods}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onClose={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

const ToastItem = ({ toast, onClose }: { toast: Toast; onClose: () => void }) => {
  const icons = {
    success: <CheckCircle className="text-[var(--color-success)]" size={20} />,
    error: <AlertCircle className="text-[var(--color-error)]" size={20} />,
    info: <Info className="text-[var(--color-info)]" size={20} />,
    warning: <AlertTriangle className="text-[var(--color-warning)]" size={20} />,
  };

  return (
    <div className="flex items-start gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-lg animate-in slide-in-from-right-full slide-out-to-right-full fade-in">
      <div className="shrink-0 mt-0.5">{icons[toast.type]}</div>
      <div className="flex-1 space-y-1">
        <h4 className="text-sm font-medium text-[var(--color-text-primary)]">{toast.title}</h4>
        {toast.description && (
          <p className="text-xs text-[var(--color-text-secondary)]">{toast.description}</p>
        )}
      </div>
      <button
        onClick={onClose}
        className="shrink-0 text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] transition-colors focus:outline-none"
      >
        <X size={16} />
      </button>
    </div>
  );
};
