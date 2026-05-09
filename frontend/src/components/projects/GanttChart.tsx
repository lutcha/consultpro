// ============================================
// GANTT CHART - Timeline visualization
// ============================================

import { useMemo } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export interface GanttItem {
  id: string;
  name: string;
  startDate: Date;
  endDate: Date;
  progress: number;
  color?: string;
  type: 'milestone' | 'task' | 'phase' | 'deliverable';
  status?: string;
}

interface GanttChartProps {
  items: GanttItem[];
  startDate?: Date;
  endDate?: Date;
  onItemClick?: (item: GanttItem) => void;
}

const statusColors: Record<string, string> = {
  completed: 'bg-green-500',
  in_progress: 'bg-blue-500',
  not_started: 'bg-gray-400',
  delayed: 'bg-red-500',
  draft: 'bg-yellow-500',
};

const typeIcons: Record<string, string> = {
  milestone: '🎯',
  task: '📋',
  phase: '📊',
  deliverable: '📦',
};

export function GanttChart({
  items,
  startDate: propStart,
  endDate: propEnd,
  onItemClick,
}: GanttChartProps) {
  const { startDate, endDate, totalDays } = useMemo(() => {
    const dates = items.flatMap((i) => [i.startDate, i.endDate]);
    const min = propStart || new Date(Math.min(...dates.map((d) => d.getTime())));
    const max = propEnd || new Date(Math.max(...dates.map((d) => d.getTime())));
    // Add some padding
    min.setDate(min.getDate() - 7);
    max.setDate(max.getDate() + 7);
    const days = Math.ceil((max.getTime() - min.getTime()) / (1000 * 60 * 60 * 24));
    return { startDate: min, endDate: max, totalDays: Math.max(days, 1) };
  }, [items, propStart, propEnd]);

  const getItemPosition = (item: GanttItem) => {
    const itemStart = Math.max(item.startDate.getTime(), startDate.getTime());
    const itemEnd = Math.min(item.endDate.getTime(), endDate.getTime());
    const offset = ((itemStart - startDate.getTime()) / (1000 * 60 * 60 * 24)) / totalDays * 100;
    const width = ((itemEnd - itemStart) / (1000 * 60 * 60 * 24)) / totalDays * 100;
    return { left: Math.max(0, offset), width: Math.max(1, width) };
  };

  const monthLabels = useMemo(() => {
    const labels: { label: string; offset: number }[] = [];
    const current = new Date(startDate);
    while (current <= endDate) {
      const offset = ((current.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) / totalDays * 100;
      labels.push({
        label: current.toLocaleDateString('pt-PT', { month: 'short', year: 'numeric' }),
        offset,
      });
      current.setMonth(current.getMonth() + 1);
      current.setDate(1);
    }
    return labels;
  }, [startDate, endDate, totalDays]);

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {/* Header with months */}
        <div className="relative h-10 border-b border-border bg-muted/50">
          {monthLabels.map((m, i) => (
            <div
              key={i}
              className="absolute top-0 h-full flex items-center px-2 text-xs font-medium text-muted-foreground border-l border-border"
              style={{ left: `${m.offset}%` }}
            >
              {m.label}
            </div>
          ))}
        </div>

        {/* Items */}
        <div className="relative">
          {items.map((item, index) => {
            const { left, width } = getItemPosition(item);
            const isMilestone = item.type === 'milestone';

            return (
              <div
                key={item.id}
                className={cn(
                  'flex items-center h-12 border-b border-border hover:bg-muted/30 transition-colors',
                  index % 2 === 0 && 'bg-muted/10'
                )}
              >
                {/* Label */}
                <div className="w-48 flex-shrink-0 px-3 flex items-center gap-2 overflow-hidden">
                  <span className="text-sm">{typeIcons[item.type]}</span>
                  <span className="text-sm font-medium truncate">{item.name}</span>
                </div>

                {/* Timeline */}
                <div className="flex-1 relative h-full">
                  {/* Today line */}
                  {(() => {
                    const today = new Date();
                    if (today >= startDate && today <= endDate) {
                      const offset = ((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) / totalDays * 100;
                      return (
                        <div
                          className="absolute top-0 bottom-0 w-px bg-red-500 z-10"
                          style={{ left: `${offset}%` }}
                        >
                          <div className="absolute -top-1 -translate-x-1/2 bg-red-500 text-white text-[10px] px-1 rounded">
                            Hoje
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}

                  {/* Item bar */}
                  <div
                    className={cn(
                      'absolute top-2 bottom-2 rounded cursor-pointer group',
                      isMilestone
                        ? 'w-4 h-4 top-4 rotate-45 bg-amber-500'
                        : item.type === 'deliverable'
                          ? cn('h-6 top-3 border-2 border-purple-500 bg-purple-100 dark:bg-purple-900/40')
                          : cn('h-6 top-3', statusColors[item.status || 'not_started'] || 'bg-blue-500')
                    )}
                    style={{ left: `${left}%`, width: isMilestone ? '16px' : `${width}%` }}
                    onClick={() => onItemClick?.(item)}
                  >
                    {/* Progress fill */}
                    {!isMilestone && item.progress > 0 && (
                      <div
                        className="absolute top-0 left-0 bottom-0 bg-white/30 rounded-l"
                        style={{ width: `${item.progress}%` }}
                      />
                    )}

                    {/* Tooltip on hover */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20">
                      <div className="bg-popover border rounded-lg shadow-lg p-3 whitespace-nowrap">
                        <p className="font-medium text-sm">{item.name}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {item.startDate.toLocaleDateString('pt-PT')} → {item.endDate.toLocaleDateString('pt-PT')}
                        </div>
                        {!isMilestone && (
                          <div className="flex items-center gap-2 mt-1 text-xs">
                            <Clock className="h-3 w-3" />
                            {item.progress}% completo
                          </div>
                        )}
                        {item.status && (
                          <Badge variant="outline" className="mt-1 text-xs">
                            {item.status}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
