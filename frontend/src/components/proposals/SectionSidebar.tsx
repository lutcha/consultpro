// ============================================
// SECTION SIDEBAR COMPONENT - Proposal Editor
// ============================================

import { CheckCircle, Circle, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ProposalSection } from '@/types';

interface SectionSidebarProps {
  sections: ProposalSection[];
  activeSection: string;
  onSectionChange: (sectionId: string) => void;
}

const sectionLabels: Record<string, string> = {
  cover: 'Capa',
  executive_summary: 'Resumo Executivo',
  methodology: 'Metodologia',
  team: 'Equipa Técnica',
  workplan: 'Plano de Trabalho',
  budget: 'Orçamento',
  annexes: 'Anexos',
};

export function SectionSidebar({
  sections,
  activeSection,
  onSectionChange,
}: SectionSidebarProps) {
  const completedCount = sections.filter((s) => s.isComplete).length;
  const progress = Math.round((completedCount / sections.length) * 100);

  return (
    <div className="w-56 bg-card border-r border-border flex flex-col">
      {/* Progress */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Progresso</span>
          <span className="text-sm text-muted-foreground">{progress}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {completedCount} de {sections.length} secções completas
        </p>
      </div>

      {/* Sections List */}
      <nav className="flex-1 py-2">
        {sections.map((section) => {
          const isActive = section.id === activeSection;
          const hasAiSuggestions = section.aiSuggestions && section.aiSuggestions.length > 0;

          return (
            <button
              key={section.id}
              onClick={() => onSectionChange(section.id)}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors text-left',
                isActive
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {section.isComplete ? (
                <CheckCircle className="h-4 w-4 text-success flex-shrink-0" />
              ) : (
                <Circle className="h-4 w-4 flex-shrink-0" />
              )}
              <span className="flex-1 truncate">
                {sectionLabels[section.type] || section.title}
              </span>
              {hasAiSuggestions && (
                <Sparkles className="h-3 w-3 text-primary flex-shrink-0" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Tips */}
      <div className="p-4 border-t border-border">
        <div className="bg-muted rounded-lg p-3">
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Dica
          </p>
          <p className="text-xs">
            Use o assistente IA para expandir e melhorar o seu texto.
          </p>
        </div>
      </div>
    </div>
  );
}
