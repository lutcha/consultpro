// ============================================
// CONSULTANTS PAGE - Consultant Database
// ============================================

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Star,
  MapPin,
  Briefcase,
  DollarSign,
  GraduationCap,
  Linkedin,
  Mail,
  Phone,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { apiGetConsultants } from '@/lib/api';
import type { ApiConsultant } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

export function Consultants() {
  const navigate = useNavigate();
  const [consultants, setConsultants] = useState<ApiConsultant[]>([]);
  const [filtered, setFiltered] = useState<ApiConsultant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedConsultant, setSelectedConsultant] = useState<ApiConsultant | null>(null);
  const [availabilityFilter, setAvailabilityFilter] = useState<string>('all');

  useEffect(() => {
    loadConsultants();
  }, []);

  useEffect(() => {
    let result = consultants;

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.email.toLowerCase().includes(q) ||
          c.skills.some((s) => s.toLowerCase().includes(q)) ||
          c.consultant_profile?.specializations.some((s) => s.toLowerCase().includes(q))
      );
    }

    if (availabilityFilter !== 'all') {
      result = result.filter((c) => c.availability === availabilityFilter);
    }

    setFiltered(result);
  }, [search, consultants, availabilityFilter]);

  const loadConsultants = async () => {
    setIsLoading(true);
    try {
      const data = await apiGetConsultants();
      setConsultants(data.results);
      setFiltered(data.results);
    } catch (err) {
      console.error('Erro ao carregar consultores:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getAvailabilityBadge = (availability: string) => {
    switch (availability) {
      case 'available':
        return (
          <Badge variant="default" className="bg-green-600">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Disponível
          </Badge>
        );
      case 'busy':
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            Ocupado
          </Badge>
        );
      case 'unavailable':
        return (
          <Badge variant="outline">
            <XCircle className="h-3 w-3 mr-1" />
            Indisponível
          </Badge>
        );
      default:
        return <Badge variant="outline">{availability}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Base de Consultores</h1>
          <p className="text-muted-foreground mt-1">
            {consultants.length} consultores registados
          </p>
        </div>
        <Button onClick={() => navigate('/consultants/new')}>
          <Briefcase className="h-4 w-4 mr-2" />
          Novo Consultor
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Pesquisar por nome, skills, especialização..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={availabilityFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAvailabilityFilter('all')}
              >
                <Filter className="h-4 w-4 mr-1" />
                Todos
              </Button>
              <Button
                variant={availabilityFilter === 'available' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAvailabilityFilter('available')}
              >
                Disponíveis
              </Button>
              <Button
                variant={availabilityFilter === 'busy' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAvailabilityFilter('busy')}
              >
                Ocupados
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{consultants.length}</p>
            <p className="text-sm text-muted-foreground">Total</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold text-green-600">
              {consultants.filter((c) => c.availability === 'available').length}
            </p>
            <p className="text-sm text-muted-foreground">Disponíveis</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold text-amber-600">
              {consultants.filter((c) => c.availability === 'busy').length}
            </p>
            <p className="text-sm text-muted-foreground">Em Projeto</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">
              {new Set(consultants.flatMap((c) => c.skills)).size}
            </p>
            <p className="text-sm text-muted-foreground">Skills Únicas</p>
          </CardContent>
        </Card>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6 h-48 bg-muted" />
            </Card>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Nenhum consultor encontrado.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((consultant) => (
            <Card
              key={consultant.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedConsultant(consultant)}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold text-lg">
                      {consultant.name?.charAt(0) || '?'}
                    </div>
                    <div>
                      <p className="font-semibold">{consultant.name}</p>
                      <p className="text-sm text-muted-foreground">{consultant.email}</p>
                    </div>
                  </div>
                  {getAvailabilityBadge(consultant.availability)}
                </div>

                <div className="mt-4 space-y-2">
                  {consultant.years_experience > 0 && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Briefcase className="h-4 w-4" />
                      {consultant.years_experience} anos experiência
                    </div>
                  )}
                  {consultant.consultant_profile?.hourly_rate && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <DollarSign className="h-4 w-4" />
                      {formatCurrency(
                        parseFloat(consultant.consultant_profile.hourly_rate),
                        consultant.consultant_profile.currency
                      )}
                      /hora
                    </div>
                  )}
                  {consultant.consultant_profile?.total_projects_completed > 0 && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Star className="h-4 w-4" />
                      {consultant.consultant_profile.total_projects_completed} projetos
                    </div>
                  )}
                </div>

                {consultant.skills.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1">
                    {consultant.skills.slice(0, 5).map((skill) => (
                      <Badge key={skill} variant="secondary" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                    {consultant.skills.length > 5 && (
                      <Badge variant="outline" className="text-xs">
                        +{consultant.skills.length - 5}
                      </Badge>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Detail Dialog */}
      <Dialog open={!!selectedConsultant} onOpenChange={() => setSelectedConsultant(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-auto">
          {selectedConsultant && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <div className="h-12 w-12 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold text-lg">
                    {selectedConsultant.name?.charAt(0) || '?'}
                  </div>
                  <div>
                    <p>{selectedConsultant.name}</p>
                    <div className="flex gap-2 mt-1">
                      {getAvailabilityBadge(selectedConsultant.availability)}
                    </div>
                  </div>
                </DialogTitle>
              </DialogHeader>

              <Tabs defaultValue="profile">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="profile">Perfil</TabsTrigger>
                  <TabsTrigger value="skills">Skills</TabsTrigger>
                  <TabsTrigger value="experience">Experiência</TabsTrigger>
                </TabsList>

                <TabsContent value="profile" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{selectedConsultant.email}</span>
                    </div>
                    {selectedConsultant.consultant_profile?.linkedin_url && (
                      <div className="flex items-center gap-2">
                        <Linkedin className="h-4 w-4 text-muted-foreground" />
                        <a
                          href={selectedConsultant.consultant_profile.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          LinkedIn
                        </a>
                      </div>
                    )}
                    {selectedConsultant.consultant_profile?.hourly_rate && (
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">
                          {formatCurrency(
                            parseFloat(selectedConsultant.consultant_profile.hourly_rate),
                            selectedConsultant.consultant_profile.currency
                          )}
                          /hora
                        </span>
                      </div>
                    )}
                    {selectedConsultant.years_experience > 0 && (
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">
                          {selectedConsultant.years_experience} anos experiência
                        </span>
                      </div>
                    )}
                  </div>

                  {selectedConsultant.consultant_profile?.education && (
                    <div>
                      <h4 className="font-medium flex items-center gap-2 mb-2">
                        <GraduationCap className="h-4 w-4" />
                        Educação
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        {selectedConsultant.consultant_profile.education}
                      </p>
                    </div>
                  )}

                  {selectedConsultant.languages.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Idiomas</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedConsultant.languages.map((lang) => (
                          <Badge key={lang} variant="outline">
                            {lang}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="skills" className="space-y-4 mt-4">
                  {selectedConsultant.skills.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Competências Técnicas</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedConsultant.skills.map((skill) => (
                          <Badge key={skill} variant="secondary">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedConsultant.consultant_profile?.specializations.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Especializações</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedConsultant.consultant_profile.specializations.map((spec) => (
                          <Badge key={spec} variant="default">
                            {spec}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="experience" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">
                          {selectedConsultant.consultant_profile?.total_projects_completed || 0}
                        </p>
                        <p className="text-sm text-muted-foreground">Projetos</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">
                          {selectedConsultant.consultant_profile?.total_proposals_won || 0}
                        </p>
                        <p className="text-sm text-muted-foreground">Propostas Ganhas</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold">
                          {selectedConsultant.consultant_profile?.performance_rating || '—'}
                        </p>
                        <p className="text-sm text-muted-foreground">Avaliação</p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
