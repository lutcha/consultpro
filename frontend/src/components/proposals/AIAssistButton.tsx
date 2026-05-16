// ============================================
// AI ASSIST BUTTON COMPONENT - wired to real backend
// ============================================

import { useState } from 'react';
import { Sparkles, Expand, Minimize2, Languages, Type, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { apiAISuggest } from '@/lib/api';
import { markdownToEditorHtml } from '@/lib/contentFormat';

interface AIAssistButtonProps {
  section: string;
  proposalId: string;
  sectionId: string;
  currentContent: string;
  onApply: (content: string) => void;
}

const suggestions = [
  {
    id: 'draft_from_context',
    label: 'Redigir a partir do ToR',
    description: 'Gera conteúdo completo com base no contexto da oportunidade',
    icon: Wand2,
  },
  {
    id: 'expand',
    label: 'Expandir parágrafo',
    description: 'Desenvolve o conteúdo com mais detalhes e exemplos',
    icon: Expand,
  },
  {
    id: 'improve',
    label: 'Melhorar redação',
    description: 'Aprimora clareza, coesão e impacto do texto',
    icon: Sparkles,
  },
  {
    id: 'summarize',
    label: 'Resumir para 100 palavras',
    description: 'Condensa o texto mantendo os pontos-chave',
    icon: Minimize2,
  },
  {
    id: 'tone_formal',
    label: 'Ajustar tom: mais formal',
    description: 'Adapta o texto para um registo mais profissional',
    icon: Type,
  },
  {
    id: 'translate_en',
    label: 'Traduzir para Inglês',
    description: 'Traduz o conteúdo mantendo o contexto técnico',
    icon: Languages,
  },
];

export function AIAssistButton({
  section,
  proposalId,
  sectionId,
  currentContent,
  onApply,
}: AIAssistButtonProps) {
  const [open, setOpen] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleApply = async (action: string) => {
    if (!proposalId || !sectionId) return;
    setIsApplying(true);
    setApplyingId(action);
    setError(null);
    try {
      const result = await apiAISuggest(proposalId, sectionId, action, currentContent);
      if (result.generated_content) {
        onApply(markdownToEditorHtml(result.generated_content));
        setOpen(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro na IA. Tente novamente.');
    } finally {
      setIsApplying(false);
      setApplyingId(null);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1 text-primary hover:text-primary hover:bg-primary/10"
        >
          <Sparkles className="h-4 w-4" />
          <span className="text-xs">IA</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-2" align="start">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground px-2 py-1">
            Assistente IA — {section}
          </p>
          {suggestions.map((suggestion) => {
            const Icon = suggestion.icon;
            const isThisApplying = isApplying && applyingId === suggestion.id;
            return (
              <Button
                key={suggestion.id}
                variant="ghost"
                className="w-full justify-start text-sm h-auto py-2 px-2"
                onClick={() => handleApply(suggestion.id)}
                disabled={isApplying}
              >
                <Icon className="mr-2 h-4 w-4 flex-shrink-0" />
                <div className="text-left">
                  <p className="font-medium">
                    {isThisApplying ? 'A gerar...' : suggestion.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {suggestion.description}
                  </p>
                </div>
              </Button>
            );
          })}
        </div>
        {isApplying && (
          <div className="mt-2 text-center">
            <p className="text-xs text-muted-foreground animate-pulse">
              A consultar IA...
            </p>
          </div>
        )}
        {error && (
          <div className="mt-2 px-2">
            <p className="text-xs text-destructive">{error}</p>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
