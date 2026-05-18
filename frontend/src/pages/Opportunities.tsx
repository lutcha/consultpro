// ============================================
// OPPORTUNITIES LIST PAGE
// ============================================

import { type FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  FileText,
  Calendar,
  Bookmark,
  Save,
  RotateCcw,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
import { formatDate, formatCurrency, getDaysUntil, cn } from '@/lib/utils';
import { useDebounce } from '@/hooks/useDebounce';
import {
  type ApiFirmProfile,
  type ApiOpportunityQueryParams,
  type ApiSavedFilter,
  apiCreateSavedFilter,
  apiGetCurrentFirmProfile,
  apiGetSavedFilters,
} from '@/lib/api';

const PROFILE_DEFAULT_VIEW = '__profile_defaults__';

type OpportunityFilterState = {
  search: string;
  sector: string;
  country: string;
  region: string;
  minScore: string;
};

type OpportunitySavedViewPayload = {
  filters?: Partial<OpportunityFilterState>;
};

const emptyFilters: OpportunityFilterState = {
  search: '',
  sector: '',
  country: '',
  region: '',
  minScore: '',
};

function humanizeSector(code: string): string {
  return code.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatList(values: string[]): string {
  if (values.length === 0) return 'sem defaults';
  return values.map((value) => value.toUpperCase()).join(', ');
}

function toQueryParams(filters: OpportunityFilterState): ApiOpportunityQueryParams {
  return {
    search: filters.search.trim(),
    sector: filters.sector.trim(),
    country: filters.country.trim(),
    region: filters.region.trim(),
    min_score: filters.minScore.trim(),
  };
}

function readSavedViewPayload(payload: Record<string, unknown>): Partial<OpportunityFilterState> {
  const candidate = payload as OpportunitySavedViewPayload;
  return candidate.filters ?? {};
}

export function Opportunities() {
  const navigate = useNavigate();
  const { opportunities, isLoading, fetchOpportunities } = useOpportunityStore();
  const [filters, setFilters] = useState<OpportunityFilterState>(emptyFilters);
  const [firmProfile, setFirmProfile] = useState<ApiFirmProfile | null>(null);
  const [savedFilters, setSavedFilters] = useState<ApiSavedFilter[]>([]);
  const [selectedSavedFilterId, setSelectedSavedFilterId] = useState(PROFILE_DEFAULT_VIEW);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [savedFilterName, setSavedFilterName] = useState('');
  const [isSavingFilter, setIsSavingFilter] = useState(false);
  const debouncedSearch = useDebounce(filters.search, 350);

  const activeFilters = useMemo(
    () => ({
      search: debouncedSearch,
      sector: filters.sector,
      country: filters.country,
      region: filters.region,
      minScore: filters.minScore,
    }),
    [debouncedSearch, filters.sector, filters.country, filters.region, filters.minScore]
  );

  useEffect(() => {
    fetchOpportunities(toQueryParams(activeFilters));
  }, [activeFilters, fetchOpportunities]);

  useEffect(() => {
    let active = true;
    async function loadSavedViews() {
      try {
        const [profile, saved] = await Promise.all([
          apiGetCurrentFirmProfile().catch(() => null),
          apiGetSavedFilters('opportunities'),
        ]);
        if (!active) return;
        setFirmProfile(profile);
        setSavedFilters(saved.results);
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Erro ao carregar vistas');
      }
    }
    loadSavedViews();
    return () => {
      active = false;
    };
  }, []);

  const updateFilter = (key: keyof OpportunityFilterState, value: string) => {
    setSelectedSavedFilterId(PROFILE_DEFAULT_VIEW);
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const applySavedFilter = (id: string) => {
    setSelectedSavedFilterId(id);
    if (id === PROFILE_DEFAULT_VIEW) {
      setFilters(emptyFilters);
      return;
    }
    const savedFilter = savedFilters.find((item) => String(item.id) === id);
    if (!savedFilter) return;
    setFilters({ ...emptyFilters, ...readSavedViewPayload(savedFilter.payload) });
  };

  const clearFilters = () => {
    setSelectedSavedFilterId(PROFILE_DEFAULT_VIEW);
    setFilters(emptyFilters);
  };

  const handleSaveFilter = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = savedFilterName.trim();
    if (!name) {
      toast.error('Nome obrigatorio');
      return;
    }
    setIsSavingFilter(true);
    try {
      const saved = await apiCreateSavedFilter({
        name,
        payload: { filters },
      });
      setSavedFilters((current) => [...current, saved].sort((a, b) => a.name.localeCompare(b.name)));
      setSelectedSavedFilterId(String(saved.id));
      setSavedFilterName('');
      setSaveDialogOpen(false);
      toast.success('Vista guardada');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao guardar vista');
    } finally {
      setIsSavingFilter(false);
    }
  };

  const getDeadlineColor = (deadline: Date) => {
    const days = getDaysUntil(deadline);
    if (days <= 3) return 'text-error font-medium';
    if (days <= 7) return 'text-warning font-medium';
    return 'text-foreground';
  };

  if (isLoading && opportunities.length === 0) {
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
          <div className="grid gap-3 lg:grid-cols-[minmax(220px,1fr)_170px_130px_120px_130px_110px_auto]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Pesquisar oportunidades..."
                className="pl-10"
                value={filters.search}
                onChange={(event) => updateFilter('search', event.target.value)}
              />
            </div>
            <Select value={selectedSavedFilterId} onValueChange={applySavedFilter}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Saved Views" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={PROFILE_DEFAULT_VIEW}>Perfil padrao</SelectItem>
                {savedFilters.map((savedFilter) => (
                  <SelectItem key={savedFilter.id} value={String(savedFilter.id)}>
                    {savedFilter.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              placeholder="Setor"
              value={filters.sector}
              onChange={(event) => updateFilter('sector', event.target.value)}
            />
            <Input
              placeholder="Pais"
              value={filters.country}
              onChange={(event) => updateFilter('country', event.target.value)}
            />
            <Input
              placeholder="Regiao"
              value={filters.region}
              onChange={(event) => updateFilter('region', event.target.value)}
            />
            <Input
              placeholder="Score min."
              inputMode="numeric"
              value={filters.minScore}
              onChange={(event) => updateFilter('minScore', event.target.value)}
            />
            <div className="flex gap-2">
              <Button variant="outline" type="button" onClick={() => setSaveDialogOpen(true)}>
                <Save className="h-4 w-4 mr-2" />
                Guardar
              </Button>
              <Button variant="ghost" size="icon" type="button" onClick={clearFilters} title="Limpar filtros">
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          </div>
          {firmProfile && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="secondary" className="gap-1">
                <Bookmark className="h-3 w-3" />
                {firmProfile.name}
              </Badge>
              <span>Setores: {formatList(firmProfile.target_sectors)}</span>
              <span>Geografias: {formatList(firmProfile.geographies)}</span>
            </div>
          )}
          <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
            <Filter className="h-3 w-3" />
            <span>{opportunities.length} oportunidades nesta vista</span>
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
            <>
              {/* Mobile card list */}
              <div className="sm:hidden space-y-3">
                {opportunities.map((opp) => (
                  <div
                    key={opp.id}
                    className="p-4 border rounded-lg cursor-pointer hover:bg-muted/50 active:bg-muted transition-colors"
                    onClick={() => navigate(`/opportunities/${opp.id}`)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium leading-snug line-clamp-2">{opp.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {humanizeSector(opp.sector)} · {opp.country.toUpperCase()}
                        </p>
                      </div>
                      <StatusBadge status={opp.status} size="sm" />
                    </div>
                    <div className="flex items-center justify-between mt-3">
                      <Badge variant="outline" className="text-xs">{opp.client}</Badge>
                      <span className={cn('text-xs', getDeadlineColor(opp.deadline))}>
                        {getDaysUntil(opp.deadline)}d · {formatDate(opp.deadline)}
                      </span>
                    </div>
                    <p className="text-sm font-semibold mt-2">
                      {formatCurrency(opp.value, opp.currency)}
                    </p>
                  </div>
                ))}
              </div>

              {/* Desktop table */}
            <div className="hidden sm:block overflow-x-auto">
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
                            {humanizeSector(opportunity.sector)} · {opportunity.country.toUpperCase()}
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
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/proposals/new?opportunity=${opportunity.id}`);
                              }}
                            >
                              <FileText className="mr-2 h-4 w-4" />
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
            </>
          )}
        </CardContent>
      </Card>

      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Guardar vista</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSaveFilter} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="saved-view-name">Nome</Label>
              <Input
                id="saved-view-name"
                value={savedFilterName}
                onChange={(event) => setSavedFilterName(event.target.value)}
                placeholder="Ex: Prioridade energia West Africa"
                autoFocus
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setSaveDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSavingFilter}>
                {isSavingFilter ? 'A guardar...' : 'Guardar'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
