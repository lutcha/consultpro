import { useEffect, useState, useCallback } from 'react';
import { Download, RefreshCw, Plus, AlertCircle, Clock, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  apiGetProposalExportRequests,
  apiCreateProposalExportRequest,
  apiRetryProposalExportRequest,
  type ApiProposalExportRequest,
} from '@/lib/api';
import { cn } from '@/lib/utils';

const EXPORT_TYPE_LABELS: Record<string, string> = {
  executive_summary: 'Sumário Executivo',
  board_pack: 'Board Pack',
  pdf: 'PDF',
  pptx: 'PowerPoint',
};

const STATUS_CONFIG: Record<
  ApiProposalExportRequest['status'],
  { label: string; color: string; icon: React.ElementType }
> = {
  queued: { label: 'Na fila', color: 'bg-amber-100 text-amber-700', icon: Clock },
  processing: { label: 'A processar', color: 'bg-blue-100 text-blue-700', icon: Loader2 },
  completed: { label: 'Concluído', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 },
  failed: { label: 'Erro', color: 'bg-red-100 text-red-700', icon: AlertCircle },
};

function formatDate(dt: string | null): string {
  if (!dt) return '—';
  return new Date(dt).toLocaleString('pt-PT', {
    day: '2-digit', month: '2-digit', year: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
}

interface Props {
  proposalId: string;
}

export function ExportRequestPanel({ proposalId }: Props) {
  const [requests, setRequests] = useState<ApiProposalExportRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [exportType, setExportType] = useState('executive_summary');
  const [retryingId, setRetryingId] = useState<number | null>(null);

  const fetchRequests = useCallback(async () => {
    try {
      const data = await apiGetProposalExportRequests(proposalId);
      setRequests(Array.isArray(data) ? data : []);
      setError('');
    } catch {
      setError('Erro ao carregar export requests.');
    } finally {
      setLoading(false);
    }
  }, [proposalId]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  // Poll while any request is queued or processing
  useEffect(() => {
    const hasPending = requests.some(
      (r) => r.status === 'queued' || r.status === 'processing'
    );
    if (!hasPending) return;
    const timer = setInterval(fetchRequests, 5000);
    return () => clearInterval(timer);
  }, [requests, fetchRequests]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const created = await apiCreateProposalExportRequest(proposalId, { export_type: exportType });
      setRequests((prev) => [created, ...prev]);
      setShowForm(false);
      setError('');
    } catch {
      setError('Erro ao criar export request.');
    } finally {
      setCreating(false);
    }
  };

  const handleRetry = async (req: ApiProposalExportRequest) => {
    setRetryingId(req.id);
    try {
      const updated = await apiRetryProposalExportRequest(proposalId, req.id);
      setRequests((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setError('');
    } catch {
      setError('Erro ao reiniciar export request.');
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0 bg-muted/20">
        <div>
          <p className="text-xs font-semibold">Exportações</p>
          <p className="text-[10px] text-muted-foreground">
            {loading ? 'A carregar...' : `${requests.length} pedido${requests.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchRequests} title="Atualizar">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1.5"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus className="h-3.5 w-3.5" />
            Novo Export
          </Button>
        </div>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="px-4 py-3 border-b border-border bg-muted/10 flex-shrink-0 space-y-2">
          <p className="text-xs font-semibold">Novo pedido de exportação</p>
          <Select value={exportType} onValueChange={setExportType}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(EXPORT_TYPE_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value} className="text-xs">
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex gap-2">
            <Button
              size="sm"
              className="h-7 text-xs flex-1"
              onClick={handleCreate}
              disabled={creating}
            >
              {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Download className="h-3.5 w-3.5 mr-1" />}
              Criar Export
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => setShowForm(false)}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {error && (
        <div className="mx-4 mt-3 flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700 flex-shrink-0">
          <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-auto px-4 py-3 space-y-2">
        {loading && (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        )}
        {!loading && requests.length === 0 && (
          <div className="text-center py-10">
            <Download className="h-8 w-8 mx-auto mb-2 text-muted-foreground/40" />
            <p className="text-xs text-muted-foreground">Nenhum export criado ainda.</p>
          </div>
        )}
        {requests.map((req) => {
          const cfg = STATUS_CONFIG[req.status] ?? STATUS_CONFIG.queued;
          const Icon = cfg.icon;
          return (
            <div
              key={req.id}
              className="rounded-lg border border-border bg-background p-3 shadow-sm space-y-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <Badge className={cn('text-[10px] gap-1 flex-shrink-0', cfg.color)}>
                    <Icon
                      className={cn(
                        'h-3 w-3',
                        req.status === 'processing' ? 'animate-spin' : ''
                      )}
                    />
                    {cfg.label}
                  </Badge>
                  <span className="text-xs font-medium truncate">
                    {EXPORT_TYPE_LABELS[req.export_type] ?? req.export_type}
                  </span>
                </div>
                {req.status === 'failed' && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 text-[10px] flex-shrink-0"
                    disabled={retryingId === req.id}
                    onClick={() => handleRetry(req)}
                  >
                    {retryingId === req.id ? (
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    ) : (
                      <RefreshCw className="h-3 w-3 mr-1" />
                    )}
                    Retry
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
                <p className="text-[10px] text-muted-foreground">
                  <span className="font-medium">Criado:</span> {formatDate(req.created_at)}
                </p>
                {req.started_at && (
                  <p className="text-[10px] text-muted-foreground">
                    <span className="font-medium">Início:</span> {formatDate(req.started_at)}
                  </p>
                )}
                {req.completed_at && (
                  <p className="text-[10px] text-muted-foreground">
                    <span className="font-medium">Fim:</span> {formatDate(req.completed_at)}
                  </p>
                )}
                {req.execution_attempts > 0 && (
                  <p className="text-[10px] text-muted-foreground">
                    <span className="font-medium">Tentativas:</span> {req.execution_attempts}
                  </p>
                )}
              </div>

              {req.requested_by_detail && (
                <p className="text-[10px] text-muted-foreground">
                  Por: {req.requested_by_detail.full_name || req.requested_by_detail.username}
                </p>
              )}

              {req.error_message && (
                <div className="rounded border border-red-200 bg-red-50 px-2 py-1">
                  <p className="text-[10px] text-red-700 line-clamp-2">{req.error_message}</p>
                </div>
              )}

              {req.executive_summary && (
                <div className="rounded border border-border bg-muted/20 px-2 py-1">
                  <p className="text-[10px] text-muted-foreground line-clamp-3">{req.executive_summary}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
