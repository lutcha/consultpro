// ============================================
// AI ASSIST BUTTON COMPONENT
// ============================================

import { useState } from 'react';
import { Sparkles, Expand, Minimize2, Languages, Type } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface AIAssistButtonProps {
  section: string;
  onApply: (action: string) => void;
}

const suggestions = [
  {
    id: 'expand',
    label: 'Expandir parágrafo',
    description: 'Desenvolve o conteúdo com mais detalhes',
    icon: Expand,
  },
  {
    id: 'summarize',
    label: 'Resumir para 100 palavras',
    description: 'Condensa o texto mantendo os pontos-chave',
    icon: Minimize2,
  },
  {
    id: 'tone-formal',
    label: 'Ajustar tom: mais formal',
    description: 'Adapta o texto para um registo mais profissional',
    icon: Type,
  },
  {
    id: 'translate-en',
    label: 'Traduzir para Inglês',
    description: 'Traduz o conteúdo mantendo o contexto técnico',
    icon: Languages,
  },
];

export function AIAssistButton({ section, onApply }: AIAssistButtonProps) {
  const [open, setOpen] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const handleApply = async (action: string) => {
    setIsApplying(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    onApply(action);
    setIsApplying(false);
    setOpen(false);
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
      <PopoverContent className="w-72 p-2" align="start">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground px-2 py-1">
            Assistente IA — {section}
          </p>
          {suggestions.map((suggestion) => {
            const Icon = suggestion.icon;
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
                  <p className="font-medium">{suggestion.label}</p>
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
              A processar...
            </p>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
