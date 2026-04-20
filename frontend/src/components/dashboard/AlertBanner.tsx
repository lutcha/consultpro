// ============================================
// ALERT BANNER COMPONENT
// ============================================

import { AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Alert } from '@/types';

interface AlertBannerProps {
  alert: Alert;
  onDismiss?: (id: string) => void;
  onResolve?: (id: string) => void;
}

export function AlertBanner({ alert, onDismiss, onResolve }: AlertBannerProps) {
  const icons = {
    warning: AlertTriangle,
    error: AlertCircle,
    info: Info,
  };

  const styles = {
    warning: 'bg-warning/10 border-warning/20 text-warning-foreground',
    error: 'bg-error/10 border-error/20 text-error-foreground',
    info: 'bg-primary/10 border-primary/20 text-primary-foreground',
  };

  const Icon = icons[alert.type];

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border',
        styles[alert.type]
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{alert.message}</p>
        {alert.action && (
          <Button
            variant="link"
            size="sm"
            className="h-auto p-0 mt-1 text-sm"
            onClick={() => onResolve?.(alert.id)}
          >
            {alert.action.label}
          </Button>
        )}
      </div>
      {onDismiss && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 flex-shrink-0"
          onClick={() => onDismiss(alert.id)}
          aria-label="Dismiss alert"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
