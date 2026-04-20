// ============================================
// QUALITY CHECK PANEL COMPONENT
// ============================================

import { CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { QCCheck, QCSuggestion } from '@/types';

interface QCPanelProps {
  checks: {
    compliance: QCCheck;
    coherence: QCCheck;
    budget: QCCheck;
    attachments: QCCheck;
  };
  overallScore: number;
  suggestions: QCSuggestion[];
  onApplySuggestion: (id: string) => void;
  onIgnoreSuggestion: (id: string) => void;
}

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

export function QCPanel({
  checks,
  overallScore,
  suggestions,
  onApplySuggestion,
  onIgnoreSuggestion,
}: QCPanelProps) {
  const [expandedChecks, setExpandedChecks] = useState<string[]>(['compliance']);

  const toggleCheck = (key: string) => {
    setExpandedChecks((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-success';
    if (score >= 70) return 'text-warning';
    return 'text-error';
  };

  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="bg-card rounded-lg border border-border p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">Pontuação Global</h3>
          <span className={cn('text-2xl font-bold', getScoreColor(overallScore))}>
            {overallScore}/100
          </span>
        </div>
        <Progress value={overallScore} className="h-2" />
        <p className="text-xs text-muted-foreground mt-2">
          {overallScore >= 85
            ? 'Proposta pronta para submissão'
            : 'Melhorias recomendadas antes da submissão'}
        </p>
      </div>

      {/* Check Categories */}
      <div className="space-y-2">
        {Object.entries(checks).map(([key, check]) => {
          const Icon = statusIcons[check.status];
          const isExpanded = expandedChecks.includes(key);

          return (
            <div
              key={key}
              className={cn(
                'rounded-lg border overflow-hidden',
                statusBgColors[check.status]
              )}
            >
              <button
                className="w-full flex items-center justify-between p-3"
                onClick={() => toggleCheck(key)}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn('h-5 w-5', statusColors[check.status])} />
                  <span className="font-medium">{checkLabels[key]}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      'text-sm font-semibold',
                      statusColors[check.status]
                    )}
                  >
                    {check.score}%
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="px-3 pb-3 space-y-2">
                  {check.items.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-2 text-sm"
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
                      <span>{item.description}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* AI Suggestions */}
      {suggestions.length > 0 && (
        <div className="bg-primary/5 rounded-lg border border-primary/20 p-4">
          <h3 className="font-semibold mb-3">Sugestões de IA</h3>
          <div className="space-y-3">
            {suggestions.map((suggestion) => (
              <div
                key={suggestion.id}
                className="bg-card rounded-lg p-3 space-y-2"
              >
                <p className="text-sm">{suggestion.text}</p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onApplySuggestion(suggestion.id)}
                  >
                    Aplicar
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onIgnoreSuggestion(suggestion.id)}
                  >
                    Ignorar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
