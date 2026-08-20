import { HTMLAttributes, forwardRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { User as UserIcon } from 'lucide-react';

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, size = 'md', ...props }, ref) => {
    const [imageError, setImageError] = useState(false);

    const sizeClasses = {
      sm: 'h-8 w-8 text-xs',
      md: 'h-10 w-10 text-sm',
      lg: 'h-12 w-12 text-base',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex shrink-0 overflow-hidden rounded-full bg-[var(--color-surface-secondary)] border border-[var(--color-border)]',
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {src && !imageError ? (
          <img
            src={src}
            alt={alt || 'Avatar'}
            className="aspect-square h-full w-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center font-medium text-[var(--color-text-secondary)]">
            {fallback ? (
              fallback.substring(0, 2).toUpperCase()
            ) : (
              <UserIcon size={size === 'sm' ? 16 : size === 'md' ? 20 : 24} />
            )}
          </div>
        )}
      </div>
    );
  }
);

Avatar.displayName = 'Avatar';
