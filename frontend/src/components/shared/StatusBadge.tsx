// ============================================
// STATUS BADGE COMPONENT
// ============================================

import { cn, getStatusColor, getStatusLabel } from '@/lib/utils';

interface StatusBadgeProps {
  status: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, className, size = 'md' }: StatusBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-0.5',
    lg: 'text-base px-3 py-1',
  };
  
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        getStatusColor(status),
        sizeClasses[size],
        className
      )}
    >
      {getStatusLabel(status)}
    </span>
  );
}
