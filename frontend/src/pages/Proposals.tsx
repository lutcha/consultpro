// ============================================
// PROPOSALS LIST PAGE
// ============================================

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Edit,
  FileCheck,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { useProposalStore } from '@/stores';
import { formatDate } from '@/lib/utils';

export function Proposals() {
  const navigate = useNavigate();
  const { proposals, isLoading, fetchProposals } = useProposalStore();

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  const calculateProgress = (proposal: (typeof proposals)[0]) => {
    if (!proposal.sections || proposal.sections.length === 0) return 0;
    const completed = proposal.sections.filter((s) => s.isComplete).length;
    return Math.round((completed / proposal.sections.length) * 100);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 w-48 bg-muted rounded animate-pulse" />
            <div className="h-4 w-64 bg-muted rounded animate-pulse mt-2" />
          </div>
          <div className="h-10 w-32 bg-muted rounded animate-pulse" />
        </div>
        <div className="h-96 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Propostas</h1>
          <p className="text-muted-foreground">
            Gerencie as propostas em desenvolvimento.
          </p>
        </div>
        <Button onClick={() => navigate('/opportunities')}>
          <Plus className="h-4 w-4 mr-2" />
          Nova Proposta
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Pesquisar propostas..." className="pl-10" />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Proposals Table */}
      <Card>
        <CardHeader>
          <CardTitle>Todas as Propostas</CardTitle>
        </CardHeader>
        <CardContent>
          {proposals.length === 0 ? (
            <EmptyState
              title="Nenhuma proposta encontrada"
              description="Comece por criar uma proposta a partir de uma oportunidade."
              actionLabel="Criar Proposta"
              onAction={() => navigate('/opportunities')}
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Título</TableHead>
                    <TableHead>Versão</TableHead>
                    <TableHead>Progresso</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Atualizado</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {proposals.map((proposal) => (
                    <TableRow
                      key={proposal.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/proposals/${proposal.id}`)}
                    >
                      <TableCell>
                        <div>
                          <p className="font-medium truncate max-w-xs">
                            {proposal.title}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {proposal.team?.length ?? 0} membros na equipa
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">v{proposal.version}</span>
                      </TableCell>
                      <TableCell>
                        <div className="w-full max-w-xs">
                          <Progress
                            value={calculateProgress(proposal)}
                            className="h-2"
                          />
                          <span className="text-xs text-muted-foreground">
                            {calculateProgress(proposal)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={proposal.status} size="sm" />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {formatDate(proposal.updatedAt)}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/proposals/${proposal.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              Ver
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/proposals/${proposal.id}/edit`);
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/proposals/${proposal.id}/qc`);
                              }}
                            >
                              <FileCheck className="mr-2 h-4 w-4" />
                              Quality Check
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
