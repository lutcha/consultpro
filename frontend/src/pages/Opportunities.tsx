// ============================================
// OPPORTUNITIES LIST PAGE
// ============================================

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  FileText,
  Calendar,
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
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { useOpportunityStore } from '@/stores';
import { formatDate, formatCurrency, getDaysUntil } from '@/lib/utils';

export function Opportunities() {
  const navigate = useNavigate();
  const { opportunities, isLoading, fetchOpportunities } = useOpportunityStore();

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const getDeadlineColor = (deadline: Date) => {
    const days = getDaysUntil(deadline);
    if (days <= 3) return 'text-error font-medium';
    if (days <= 7) return 'text-warning font-medium';
    return 'text-foreground';
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
          <h1 className="text-2xl font-bold tracking-tight">Oportunidades</h1>
          <p className="text-muted-foreground">
            Gerencie as oportunidades de consultoria internacional.
          </p>
        </div>
        <Button onClick={() => navigate('/opportunities/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Nova Oportunidade
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Pesquisar oportunidades..."
                className="pl-10"
              />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Opportunities Table */}
      <Card>
        <CardHeader>
          <CardTitle>Todas as Oportunidades</CardTitle>
        </CardHeader>
        <CardContent>
          {opportunities.length === 0 ? (
            <EmptyState
              title="Nenhuma oportunidade encontrada"
              description="Comece por adicionar uma nova oportunidade."
              actionLabel="Adicionar Oportunidade"
              onAction={() => navigate('/opportunities/new')}
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Título</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Valor</TableHead>
                    <TableHead>Prazo</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {opportunities.map((opportunity) => (
                    <TableRow
                      key={opportunity.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() =>
                        navigate(`/opportunities/${opportunity.id}`)
                      }
                    >
                      <TableCell>
                        <div>
                          <p className="font-medium truncate max-w-xs">
                            {opportunity.title}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {opportunity.sector} • {opportunity.country}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{opportunity.client}</Badge>
                      </TableCell>
                      <TableCell>
                        {formatCurrency(
                          opportunity.value,
                          opportunity.currency
                        )}
                      </TableCell>
                      <TableCell>
                        <div className={getDeadlineColor(opportunity.deadline)}>
                          <p>{formatDate(opportunity.deadline)}</p>
                          <p className="text-xs">
                            {getDaysUntil(opportunity.deadline)} dias restantes
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={opportunity.status} size="sm" />
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
                                navigate(`/opportunities/${opportunity.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              Ver Detalhes
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/opportunities/${opportunity.id}/edit`);
                              }}
                            >
                              <FileText className="mr-2 h-4 w-4" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                // Create proposal from opportunity
                              }}
                            >
                              <Calendar className="mr-2 h-4 w-4" />
                              Criar Proposta
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
