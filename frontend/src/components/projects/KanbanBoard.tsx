// ============================================
// KANBAN BOARD - Jira-like task board
// ============================================

import { useState } from 'react';
import { Plus, MoreHorizontal, Calendar, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

export interface KanbanTask {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee?: string;
  dueDate?: string;
  tags?: string[];
}

export interface KanbanColumn {
  id: string;
  title: string;
  color?: string;
}

interface KanbanBoardProps {
  columns: KanbanColumn[];
  tasks: KanbanTask[];
  onTaskMove?: (taskId: string, newStatus: string) => void;
  onTaskClick?: (task: KanbanTask) => void;
  onAddTask?: (columnId: string) => void;
}

const priorityColors: Record<string, string> = {
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  critical: 'bg-red-100 text-red-800 border-red-200',
};

const priorityLabels: Record<string, string> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
  critical: 'Crítica',
};

export function KanbanBoard({
  columns,
  tasks,
  onTaskMove,
  onTaskClick,
  onAddTask,
}: KanbanBoardProps) {
  const [draggedTask, setDraggedTask] = useState<string | null>(null);

  const handleDragStart = (taskId: string) => {
    setDraggedTask(taskId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    if (draggedTask && onTaskMove) {
      onTaskMove(draggedTask, columnId);
      setDraggedTask(null);
    }
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((column) => {
        const columnTasks = tasks.filter((t) => t.status === column.id);

        return (
          <div
            key={column.id}
            className="flex-shrink-0 w-[260px] sm:w-80 flex flex-col"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, column.id)}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-sm">{column.title}</h3>
                <Badge variant="secondary" className="text-xs">
                  {columnTasks.length}
                </Badge>
              </div>
              {onAddTask && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => onAddTask(column.id)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Tasks */}
            <div className="space-y-3 min-h-[100px]">
              {columnTasks.map((task) => (
                <Card
                  key={task.id}
                  draggable
                  onDragStart={() => handleDragStart(task.id)}
                  className={cn(
                    'cursor-pointer hover:shadow-md transition-shadow border-l-4',
                    draggedTask === task.id && 'opacity-50',
                    task.priority === 'critical' && 'border-l-red-500',
                    task.priority === 'high' && 'border-l-orange-500',
                    task.priority === 'medium' && 'border-l-yellow-500',
                    task.priority === 'low' && 'border-l-blue-500'
                  )}
                  onClick={() => onTaskClick?.(task)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between">
                      <p className="font-medium text-sm">{task.title}</p>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-6 w-6 p-0 -mr-1">
                            <MoreHorizontal className="h-3 w-3" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {columns
                            .filter((c) => c.id !== column.id)
                            .map((c) => (
                              <DropdownMenuItem
                                key={c.id}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onTaskMove?.(task.id, c.id);
                                }}
                              >
                                Mover para {c.title}
                              </DropdownMenuItem>
                            ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {task.description && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {task.description}
                      </p>
                    )}

                    <div className="flex items-center justify-between mt-3">
                      <Badge
                        variant="outline"
                        className={cn('text-xs', priorityColors[task.priority])}
                      >
                        {priorityLabels[task.priority]}
                      </Badge>

                      <div className="flex items-center gap-2 text-muted-foreground">
                        {task.assignee && (
                          <div className="flex items-center gap-1" title={task.assignee}>
                            <User className="h-3 w-3" />
                          </div>
                        )}
                        {task.dueDate && (
                          <div className="flex items-center gap-1 text-xs">
                            <Calendar className="h-3 w-3" />
                            {task.dueDate}
                          </div>
                        )}
                      </div>
                    </div>

                    {task.tags && task.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {task.tags.map((tag) => (
                          <span
                            key={tag}
                            className="text-xs px-1.5 py-0.5 bg-muted rounded text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
