// ============================================
// ACTIVITY TIMELINE COMPONENT
// ============================================

import { FileText, Briefcase, CheckCircle, MessageSquare } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { cn, formatDate } from '@/lib/utils';
import type { Activity } from '@/types';

interface ActivityTimelineProps {
  activities: Activity[];
  className?: string;
}

const activityIcons = {
  proposal_created: FileText,
  proposal_updated: FileText,
  opportunity_added: Briefcase,
  qc_completed: CheckCircle,
  comment_added: MessageSquare,
};

const activityColors = {
  proposal_created: 'bg-primary/10 text-primary',
  proposal_updated: 'bg-primary/10 text-primary',
  opportunity_added: 'bg-accent/10 text-accent',
  qc_completed: 'bg-success/10 text-success',
  comment_added: 'bg-warning/10 text-warning',
};

export function ActivityTimeline({ activities, className }: ActivityTimelineProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {activities.map((activity, index) => {
        const Icon = activityIcons[activity.type];
        const isLast = index === activities.length - 1;

        return (
          <div key={activity.id} className="flex gap-4">
            {/* Timeline line */}
            {!isLast && (
              <div className="absolute left-6 top-10 bottom-0 w-px bg-border" />
            )}

            {/* Icon */}
            <div
              className={cn(
                'h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0',
                activityColors[activity.type]
              )}
            >
              <Icon className="h-5 w-5" />
            </div>

            {/* Content */}
            <div className="flex-1 pb-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Avatar className="h-6 w-6">
                    <AvatarImage
                      src={activity.user.avatar}
                      alt={activity.user.name}
                    />
                    <AvatarFallback>{activity.user.name.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium">{activity.user.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDate(activity.timestamp)}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {activity.description}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
