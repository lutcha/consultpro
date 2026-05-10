// ============================================
// PROPOSAL TABLE COMPONENT
// ============================================

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MoreHorizontal, Eye, Edit, FileCheck } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { formatDate, formatCurrency, getDaysUntil } from '@/lib/utils';
import type { PipelineItem } from '@/types';

interface ProposalTableProps {
  proposals: PipelineItem[];
}

export function ProposalTable({ proposals }: ProposalTableProps) {
  const navigate = useNavigate();
  const [sortConfig, setSortConfig] = useState<{
    key: keyof PipelineItem;
    direction: 'asc' | 'desc';
  } | null>(null);

  const handleSort = (key: keyof PipelineItem) => {
    setSortConfig((current) => {
      if (current?.key === key) {
        return { key, direction: current.direction === 'asc' ? 'desc' : 'asc' };
      }
      return { key, direction: 'asc' };
    });
  };

  const sortedProposals = [...proposals].sort((a, b) => {
    if (!sortConfig) return 0;

    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];

    if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const getDeadlineColor = (deadline: Date) => {
    const days = getDaysUntil(deadline);
    if (days <= 3) return 'text-error font-medium';
    if (days <= 7) return 'text-warning font-medium';
    return 'text-foreground';
  };

  if (proposals.length === 0) {
    return (
      <EmptyState
        title="Nenhuma proposta encontrada"
        description="Comece por criar uma nova proposta a partir de uma oportunidade."
        actionLabel="Criar Proposta"
        onAction={() => navigate('/opportunities')}
      />
    );
  }

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead
              className="cursor-pointer"
              onClick={() => handleSort('title')}
            >
              Título
            </TableHead>
            <TableHead
              className="cursor-pointer"
              onClick={() => handleSort('client')}
            >
              Cliente
            </TableHead>
            <TableHead
              className="cursor-pointer"
              onClick={() => handleSort('deadline')}
            >
              Prazo
            </TableHead>
            <TableHead>Progresso</TableHead>
            <TableHead
              className="cursor-pointer"
              onClick={() => handleSort('status')}
            >
              Estado
            </TableHead>
            <TableHead className="text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedProposals.map((proposal) => (
            <TableRow
              key={proposal.id}
              className="table-row-hover cursor-pointer"
              onClick={() => navigate(`/proposals/${proposal.id}`)}
            >
              <TableCell className="font-medium">
                <div>
                  <p className="truncate max-w-xs">{proposal.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatCurrency(proposal.value, 'USD')}
                  </p>
                </div>
              </TableCell>
              <TableCell>{proposal.client}</TableCell>
              <TableCell>
                <div className={getDeadlineColor(proposal.deadline)}>
                  <p>{formatDate(proposal.deadline)}</p>
                  <p className="text-xs">
                    {getDaysUntil(proposal.deadline)} dias restantes
                  </p>
                </div>
              </TableCell>
              <TableCell>
                <div className="w-full max-w-xs">
                  <Progress value={proposal.progress} className="h-2" />
                  <span className="text-xs text-muted-foreground">
                    {proposal.progress}%
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <StatusBadge status={proposal.status} size="sm" />
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
  );
}
