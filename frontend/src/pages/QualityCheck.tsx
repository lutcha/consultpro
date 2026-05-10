// ============================================
// QUALITY CHECK PAGE
// ============================================

import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  RefreshCw,
  Download,
  CheckCircle,
  AlertTriangle,
  XCircle,
  FileCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useQCStore, useProposalStore } from '@/stores';
import { cn } from '@/lib/utils';

const checkLabels: Record<string, string> = {
  compliance: 'Conformidade com ToR',
  coherence: 'Coerência Narrativa',
  budget: 'Orçamento',
  attachments: 'Anexos',
};

const statusIcons = {
  pass: CheckCircle,
  warn: AlertTriangle,
  fail: XCircle,
};

const statusColors = {
  pass: 'text-success',
  warn: 'text-warning',
  fail: 'text-error',
};

const statusBgColors = {
  pass: 'bg-success/10 border-success/20',
  warn: 'bg-warning/10 border-warning/20',
  fail: 'bg-error/10 border-error/20',
};

const statusLabels = {
  pass: 'Aprovado',
  warn: 'Atenção',
  fail: 'Reprovado',
};

export function QualityCheck() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { qcState, isRunning, runQC, applySuggestion, ignoreSuggestion, canSubmit } =
    useQCStore();
  const { selectedProposal, selectProposal } = useProposalStore();

  useEffect(() => {
    if (id) {
      selectProposal(id);
      runQC(id);
    }
  }, [id, selectProposal, runQC]);

  if (isRunning || !qcState) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <RefreshCw className="h-12 w-12 text-primary animate-spin mb-4" />
        <h2 className="text-xl font-semibold">A executar Quality Check...</h2>
        <p className="text-muted-foreground">
          A analisar a proposta segundo os critérios do ToR
        </p>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-success';
    if (score >= 70) return 'text-warning';
    return 'text-error';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/proposals/${id}`)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar ao Editor
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FileCheck className="h-6 w-6 text-primary" />
              Quality Check
            </h1>
            <p className="text-muted-foreground">
              {selectedProposal?.title}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={() => runQC(id!)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Re-run QC
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Exportar Report
          </Button>
          <Button disabled={!canSubmit()}>
            <CheckCircle className="h-4 w-4 mr-2" />
            Aprovar
          </Button>
        </div>
      </div>

      {/* Overall Score */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold">Pontuação Global</h2>
                <span
                  className={cn(
                    'text-4xl font-bold',
                    getScoreColor(qcState.overallScore)
                  )}
                >
                  {qcState.overallScore}/100
                </span>
              </div>
              <Progress value={qcState.overallScore} className="h-3" />
              <p className="text-sm text-muted-foreground mt-2">
                {qcState.overallScore >= 85
                  ? 'Proposta pronta para submissão'
                  : qcState.overallScore >= 70
                  ? 'Melhorias recomendadas antes da submissão'
                  : 'Revisões necessárias antes da submissão'}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-success">
                  {
                    Object.values(qcState.checks).filter(
                      (c) => c.status === 'pass'
                    ).length
                  }
                </div>
                <div className="text-xs text-muted-foreground">Aprovados</div>
              </div>
              <Separator orientation="vertical" className="h-10" />
              <div className="text-center">
                <div className="text-2xl font-bold text-warning">
                  {
                    Object.values(qcState.checks).filter(
                      (c) => c.status === 'warn'
                    ).length
                  }
                </div>
                <div className="text-xs text-muted-foreground">Atenção</div>
              </div>
              <Separator orientation="vertical" className="h-10" />
              <div className="text-center">
                <div className="text-2xl font-bold text-error">
                  {
                    Object.values(qcState.checks).filter(
                      (c) => c.status === 'fail'
                    ).length
                  }
                </div>
                <div className="text-xs text-muted-foreground">Reprovados</div>
              </div>
            </div>
          </div>

          {!canSubmit() && (
            <div className="mt-4 p-3 bg-error/10 border border-error/20 rounded-lg flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-error" />
              <p className="text-sm text-error">
                Score &lt; 85 bloqueia submissão. Revise os itens assinalados.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Check Categories */}
      <div className="grid lg:grid-cols-2 gap-6">
        {Object.entries(qcState.checks).map(([key, check]) => {
          const Icon = statusIcons[check.status];

          return (
            <Card key={key}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Icon className={cn('h-5 w-5', statusColors[check.status])} />
                    {checkLabels[key]}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'text-lg font-bold',
                        statusColors[check.status]
                      )}
                    >
                      {check.score}%
                    </span>
                    <Badge
                      variant="outline"
                      className={statusBgColors[check.status]}
                    >
                      {statusLabels[check.status]}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {check.items.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-3 p-2 rounded-lg bg-muted/50"
                    >
                      {item.status === 'pass' && (
                        <CheckCircle className="h-4 w-4 text-success flex-shrink-0 mt-0.5" />
                      )}
                      {item.status === 'warn' && (
                        <AlertTriangle className="h-4 w-4 text-warning flex-shrink-0 mt-0.5" />
                      )}
                      {item.status === 'fail' && (
                        <XCircle className="h-4 w-4 text-error flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm">{item.description}</p>
                        {item.section && (
                          <Badge variant="outline" className="mt-1 text-xs">
                            {item.section}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* AI Suggestions */}
      {qcState.suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-lg">💡</span>
              Sugestões de IA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {qcState.suggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  className="flex items-start justify-between p-4 bg-primary/5 border border-primary/20 rounded-lg"
                >
                  <div>
                    <p className="text-sm">{suggestion.text}</p>
                    <Badge variant="outline" className="mt-2 text-xs">
                      {suggestion.targetSection}
                    </Badge>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => applySuggestion(suggestion.id)}
                    >
                      Aplicar
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => ignoreSuggestion(suggestion.id)}
                    >
                      Ignorar
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Footer */}
      <div className="flex justify-between items-center pt-4 border-t border-border">
        <Button
          variant="outline"
          onClick={() => navigate(`/proposals/${id}`)}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar ao Editor
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => runQC(id!)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Re-run QC
          </Button>
          <Button disabled={!canSubmit()}>
            <CheckCircle className="h-4 w-4 mr-2" />
            Aprovar para Submissão
          </Button>
        </div>
      </div>
    </div>
  );
}
