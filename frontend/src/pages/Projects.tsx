// ============================================
// PROJECTS LIST PAGE
// ============================================

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Play,
  CheckCircle,
  PauseCircle,
  AlertTriangle,
  Calendar,
  DollarSign,
  Users,
  ArrowLeft,
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
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { apiGetProjects, apiGetProjectStats } from '@/lib/api';
import type { ApiProject } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [stats, setStats] = useState({
    total_projects: 0,
    active_projects: 0,
    planning_projects: 0,
    completed_projects: 0,
    overdue_projects: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [projectsRes, statsRes] = await Promise.all([
        apiGetProjects(),
        apiGetProjectStats(),
      ]);
      setProjects(projectsRes.results);
      setStats(statsRes);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Play className="h-4 w-4 text-success" />;
      case 'planning': return <Calendar className="h-4 w-4 text-blue-500" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-success" />;
      case 'on_hold': return <PauseCircle className="h-4 w-4 text-warning" />;
      default: return null;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Projetos</h1>
            <p className="text-muted-foreground">
              Gestão do ciclo de vida dos projetos.
            </p>
          </div>
        </div>
        <Button onClick={() => navigate('/projects/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Projeto
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total</p>
            <p className="text-2xl font-bold">{stats.total_projects}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Em Execução</p>
            <p className="text-2xl font-bold text-success">{stats.active_projects}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Em Planeamento</p>
            <p className="text-2xl font-bold text-blue-500">{stats.planning_projects}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Concluídos</p>
            <p className="text-2xl font-bold text-green-600">{stats.completed_projects}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Atrasados</p>
            <p className="text-2xl font-bold text-destructive">{stats.overdue_projects}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Pesquisar projetos..." className="pl-10" />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Projects Table */}
      <Card>
        <CardHeader>
          <CardTitle>Todos os Projetos</CardTitle>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <EmptyState
              title="Nenhum projeto encontrado"
              description="Crie um novo projeto a partir de uma proposta ganha."
              actionLabel="Criar Projeto"
              onAction={() => navigate('/projects/new')}
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Projeto</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Progresso</TableHead>
                    <TableHead>Orçamento</TableHead>
                    <TableHead>Prazo</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projects.map((project) => (
                    <TableRow
                      key={project.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <TableCell>
                        <div>
                          <p className="font-medium">{project.title}</p>
                          <p className="text-sm text-muted-foreground">
                            {project.sector} • {project.country}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>{project.client}</TableCell>
                      <TableCell>
                        <div className="w-full max-w-xs">
                          <Progress value={project.progress} className="h-2" />
                          <span className="text-xs text-muted-foreground">
                            {project.progress}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <DollarSign className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">
                            {parseFloat(project.budget_total).toLocaleString()} {project.budget_currency}
                          </span>
                        </div>
                        {project.budget_utilization > 0 && (
                          <p className="text-xs text-muted-foreground">
                            Utilizado: {project.budget_utilization}%
                          </p>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">
                            {project.end_date ? formatDate(new Date(project.end_date)) : '—'}
                          </span>
                        </div>
                        {project.is_overdue && (
                          <Badge variant="destructive" className="text-xs mt-1">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Atrasado
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(project.status)}
                          <StatusBadge status={project.status} size="sm" />
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
                                navigate(`/projects/${project.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              Ver Detalhes
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
