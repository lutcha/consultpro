// ============================================
// REPORT MODAL — period selector
// ============================================

import { useState } from 'react';
import { FileText, BarChart3, CalendarDays } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ReportPreview, type ReportPeriod } from './ReportPreview';
import type { DashboardStats, PipelineItem, FunnelData, User } from '@/types';

interface ReportModalProps {
  open: boolean;
  onClose: () => void;
  stats: DashboardStats | null;
  pipeline: PipelineItem[];
  funnel: FunnelData | null;
  user: User | null;
}

const PERIODS: { value: ReportPeriod; label: string; description: string; Icon: React.ElementType }[] = [
  { value: 'weekly',    label: 'Semanal',      description: 'Últimos 7 dias',       Icon: CalendarDays },
  { value: 'monthly',   label: 'Mensal',       description: 'Mês actual',           Icon: BarChart3 },
  { value: 'quarterly', label: 'Trimestral',   description: 'Trimestre actual',     Icon: FileText },
];

export function ReportModal({ open, onClose, stats, pipeline, funnel, user }: ReportModalProps) {
  const [selected, setSelected] = useState<ReportPeriod>('monthly');
  const [showReport, setShowReport] = useState(false);

  const handleClose = () => {
    setShowReport(false);
    onClose();
  };

  if (showReport && stats) {
    return (
      <ReportPreview
        stats={stats}
        pipeline={pipeline}
        funnel={funnel}
        user={user}
        period={selected}
        onClose={handleClose}
      />
    );
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-primary" />
            Gerar Relatório
          </DialogTitle>
        </DialogHeader>

        <p className="text-sm text-muted-foreground -mt-1">
          Selecione o período de análise. O relatório é gerado com os dados actuais do dashboard.
        </p>

        <div className="space-y-2 py-1">
          {PERIODS.map(({ value, label, description, Icon }) => {
            const active = selected === value;
            return (
              <button
                key={value}
                onClick={() => setSelected(value)}
                className={`w-full flex items-center gap-3 p-3.5 rounded-xl border-2 text-left transition-all duration-150 ${
                  active
                    ? 'border-primary bg-primary/5 shadow-sm'
                    : 'border-border hover:border-primary/30 hover:bg-muted/40'
                }`}
              >
                <div className={`p-2 rounded-lg transition-colors ${
                  active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                }`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold">{label}</div>
                  <div className="text-xs text-muted-foreground">{description}</div>
                </div>
                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors ${
                  active ? 'border-primary bg-primary' : 'border-muted-foreground/30'
                }`}>
                  {active && <div className="w-1.5 h-1.5 rounded-full bg-primary-foreground" />}
                </div>
              </button>
            );
          })}
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="outline" size="sm" onClick={handleClose}>
            Cancelar
          </Button>
          <Button
            size="sm"
            onClick={() => setShowReport(true)}
            disabled={!stats}
            className="bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-500 hover:to-blue-500 border-0"
          >
            <FileText className="h-3.5 w-3.5 mr-1.5" />
            Gerar Relatório
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
