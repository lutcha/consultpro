// ============================================
// OPPORTUNITY DETAIL PAGE
// ============================================

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  MessageSquare,
  Download,
  CheckSquare,
  AlertTriangle,
  FileText,
  Grid3X3,
  ShieldAlert,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useOpportunityStore } from '@/stores';
import { formatDate, formatCurrency, cn } from '@/lib/utils';
import type { Requirement, Risk } from '@/types';

export function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedOpportunity, selectOpportunity, updateStatus, isLoading } =
    useOpportunityStore();
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    if (id) {
      selectOpportunity(id);
    }
  }, [id]);

  const opportunity = selectedOpportunity;

  if (isLoading) {
    return <OpportunityDetailSkeleton />;
  }

  if (!opportunity) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Oportunidade não encontrada.</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/opportunities')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
      </div>
    );
  }

  const handleGo = async () => {
    await updateStatus(opportunity.id, 'go');
  };

  const handleNoGo = async () => {
    await updateStatus(opportunity.id, 'no_go');
  };

  const requirementsByCategory = opportunity.requirements.reduce(
    (acc, req) => {
      if (!acc[req.category]) acc[req.category] = [];
      acc[req.category].push(req);
      return acc;
    },
    {} as Record<string, Requirement[]>
  );

  const categoryLabels: Record<string, string> = {
    functional: 'Funcionais',
    technical: 'Técnicos',
    institutional: 'Institucionais',
    financial: 'Financeiros',
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb & Header */}
      <div className="space-y-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/opportunities')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar às Oportunidades
        </Button>

        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{opportunity.title}</h1>
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline">{opportunity.client}</Badge>
              <Badge variant="outline">{opportunity.sector}</Badge>
              <Badge variant="outline">{opportunity.country}</Badge>
              <StatusBadge status={opportunity.status} size="sm" />
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-primary">
              {formatCurrency(opportunity.value, opportunity.currency)}
            </p>
            <p className="text-sm text-muted-foreground">
              Prazo: {formatDate(opportunity.deadline)}
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <Button
          onClick={handleGo}
          className="bg-success hover:bg-success/90"
          disabled={opportunity.status === 'go'}
        >
          <CheckCircle className="h-4 w-4 mr-2" />
          Go — Avançar
        </Button>
        <Button
          variant="outline"
          onClick={handleNoGo}
          disabled={opportunity.status === 'no_go'}
          className="border-error text-error hover:bg-error/10"
        >
          <XCircle className="h-4 w-4 mr-2" />
          No-Go — Arquivar
        </Button>
        <Button variant="outline">
          <MessageSquare className="h-4 w-4 mr-2" />
          Adicionar Nota
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="summary" className="gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">Resumo</span>
          </TabsTrigger>
          <TabsTrigger value="tor" className="gap-2">
            <FileText className="h-4 w-4" />
            <span className="hidden sm:inline">ToR</span>
          </TabsTrigger>
          <TabsTrigger value="matrix" className="gap-2">
            <Grid3X3 className="h-4 w-4" />
            <span className="hidden sm:inline">Matriz</span>
          </TabsTrigger>
          <TabsTrigger value="risks" className="gap-2">
            <ShieldAlert className="h-4 w-4" />
            <span className="hidden sm:inline">Riscos</span>
          </TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          {/* AI Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-lg">🤖</span>
                Resumo IA
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Este ToR foca-se em {opportunity.sector.toLowerCase()}, com ênfase em 
                resultados mensuráveis e sustentabilidade. Prazo:{' '}
                {formatDate(opportunity.deadline)}. Critérios QCBS: Técnica 70%, 
                Financeira 30%.
              </p>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" size="sm">
                  Regenerar
                </Button>
                <Button variant="outline" size="sm">
                  Editar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Requirements */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Requisitos Extraídos</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <CheckSquare className="h-4 w-4 mr-2" />
                    Validar Todos
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Exportar CSV
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="w-full">
                {Object.entries(requirementsByCategory).map(
                  ([category, reqs]) => (
                    <AccordionItem key={category} value={category}>
                      <AccordionTrigger>
                        <div className="flex items-center gap-2">
                          <span>{categoryLabels[category] || category}</span>
                          <Badge variant="secondary" className="text-xs">
                            {reqs.length}
                          </Badge>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-2">
                          {reqs.map((req) => (
                            <div
                              key={req.id}
                              className="flex items-start gap-3 p-2 rounded-lg bg-muted/50"
                            >
                              <CheckSquare
                                className={cn(
                                  'h-5 w-5 flex-shrink-0',
                                  req.isCovered
                                    ? 'text-success'
                                    : 'text-muted-foreground'
                                )}
                              />
                              <div className="flex-1">
                                <p className="text-sm">{req.description}</p>
                                <Badge variant="outline" className="mt-1 text-xs">
                                  {req.priority}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  )
                )}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ToR Tab */}
        <TabsContent value="tor">
          <Card>
            <CardHeader>
              <CardTitle>Termos de Referência</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <p className="text-muted-foreground whitespace-pre-line">
                  {opportunity.description}
                </p>
              </div>
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">
                  Documento completo disponível para download.
                </p>
                <Button variant="outline" className="mt-2">
                  <Download className="h-4 w-4 mr-2" />
                  Descarregar ToR (PDF)
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Matrix Tab */}
        <TabsContent value="matrix">
          <Card>
            <CardHeader>
              <CardTitle>Matriz de Dissecação</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left p-2">Requisito</th>
                      <th className="text-left p-2">Prioridade</th>
                      <th className="text-left p-2">Coberto em</th>
                      <th className="text-left p-2">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opportunity.requirements.map((req) => (
                      <tr key={req.id} className="border-b border-border">
                        <td className="p-2">{req.description}</td>
                        <td className="p-2">
                          <Badge variant="outline">{req.priority}</Badge>
                        </td>
                        <td className="p-2">
                          {req.coveredIn || '—'}
                        </td>
                        <td className="p-2">
                          {req.isCovered ? (
                            <CheckCircle className="h-5 w-5 text-success" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-warning" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risks Tab */}
        <TabsContent value="risks">
          <Card>
            <CardHeader>
              <CardTitle>Análise de Riscos</CardTitle>
            </CardHeader>
            <CardContent>
              {opportunity.risks.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum risco identificado.
                </p>
              ) : (
                <div className="space-y-4">
                  {opportunity.risks.map((risk) => (
                    <RiskCard key={risk.id} risk={risk} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function RiskCard({ risk }: { risk: Risk }) {
  const severityColors = {
    low: 'bg-success/10 border-success/20 text-success',
    medium: 'bg-warning/10 border-warning/20 text-warning',
    high: 'bg-error/10 border-error/20 text-error',
  };

  const severityLabels = {
    low: 'Baixo',
    medium: 'Médio',
    high: 'Alto',
  };

  return (
    <div
      className={`p-4 rounded-lg border ${severityColors[risk.severity]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">{risk.description}</p>
          {risk.mitigation && (
            <p className="text-sm mt-2 opacity-80">
              <strong>Mitigação:</strong> {risk.mitigation}
            </p>
          )}
        </div>
        <Badge variant="outline">{severityLabels[risk.severity]}</Badge>
      </div>
    </div>
  );
}

function OpportunityDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-32" />
      <div className="space-y-2">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-6 w-1/2" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-32" />
      </div>
      <Skeleton className="h-96" />
    </div>
  );
}
