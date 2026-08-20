import { cn } from '@/lib/utils';
import { HTMLAttributes } from 'react';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
}

export function Skeleton({
  className,
  variant = 'text',
  ...props
}: SkeletonProps) {
  const variants = {
    text: 'h-4 w-full rounded-[var(--radius-sm)]',
    circular: 'rounded-full',
    rectangular: 'rounded-[var(--radius-md)]',
  };

  return (
    <div
      className={cn(
        'animate-pulse bg-[var(--color-surface-tertiary)]',
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
