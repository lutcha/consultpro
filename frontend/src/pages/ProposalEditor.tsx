// ============================================
// PROPOSAL EDITOR PAGE
// ============================================

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Send,
  Users,
  CheckCircle,
  ChevronRight,
  FileText,
  CheckSquare,
  Lightbulb,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
// import { CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { SectionSidebar } from '@/components/proposals/SectionSidebar';
import { AIAssistButton } from '@/components/proposals/AIAssistButton';
import { useProposalStore } from '@/stores';
// import { cn } from '@/lib/utils';

// Toolbar buttons for the editor
const toolbarButtons = [
  { label: 'B', action: 'bold', title: 'Negrito' },
  { label: 'I', action: 'italic', title: 'Itálico' },
  { label: 'U', action: 'underline', title: 'Sublinhado' },
  { label: '•', action: 'bullet', title: 'Lista' },
  { label: '1.', action: 'numbered', title: 'Lista Numerada' },
  { label: '🔗', action: 'link', title: 'Link' },
];

export function ProposalEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedProposal, selectProposal, updateSection, autoSaveStatus } =
    useProposalStore();
  const [activeSectionId, setActiveSectionId] = useState<string>('');
  const [editorContent, setEditorContent] = useState('');

  useEffect(() => {
    if (id) {
      selectProposal(id);
    }
  }, [id, selectProposal]);

  useEffect(() => {
    if (selectedProposal && selectedProposal.sections.length > 0) {
      if (!activeSectionId) {
        setActiveSectionId(selectedProposal.sections[0].id);
      }
      const section = selectedProposal.sections.find(
        (s) => s.id === activeSectionId
      );
      if (section) {
        setEditorContent(section.content);
      }
    }
  }, [selectedProposal, activeSectionId]);

  const handleSectionChange = (sectionId: string) => {
    // Save current section before switching
    if (activeSectionId && editorContent) {
      updateSection(selectedProposal!.id, activeSectionId, editorContent);
    }
    setActiveSectionId(sectionId);
  };

  const handleContentChange = (content: string) => {
    setEditorContent(content);
    // Auto-save after delay
    const timeoutId = setTimeout(() => {
      if (selectedProposal) {
        updateSection(selectedProposal.id, activeSectionId, content);
      }
    }, 1000);
    return () => clearTimeout(timeoutId);
  };

  const handleAISuggestion = (action: string) => {
    // Simulate AI processing
    const suggestions: Record<string, string> = {
      expand:
        editorContent +
        '\n\n[Conteúdo expandido pela IA com mais detalhes e contexto relevante para esta secção.]',
      summarize:
        '[Versão resumida do texto original, mantendo os pontos-chave e eliminando redundâncias.]',
      'tone-formal':
        '[Versão com tom mais formal e profissional do texto original, adequada para submissão a organismos internacionais.]',
      'translate-en':
        '[English translation of the original text, maintaining technical terminology and professional tone.]',
    };

    setEditorContent(suggestions[action] || editorContent);
    if (selectedProposal) {
      updateSection(
        selectedProposal.id,
        activeSectionId,
        suggestions[action] || editorContent
      );
    }
  };

  const activeSection = selectedProposal?.sections.find(
    (s) => s.id === activeSectionId
  );

  if (!selectedProposal) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Proposta não encontrada.</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/proposals')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/dashboard')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-xl font-bold">{selectedProposal.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">v{selectedProposal.version}</Badge>
              <Badge
                variant={
                  autoSaveStatus === 'saved' ? 'default' : 'secondary'
                }
                className="text-xs"
              >
                {autoSaveStatus === 'saving' && 'A guardar...'}
                {autoSaveStatus === 'saved' && 'Guardado'}
                {autoSaveStatus === 'idle' && 'Rascunho'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 mr-4">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">3 online</span>
          </div>
          <Button variant="outline" size="sm">
            <Save className="h-4 w-4 mr-2" />
            Guardar
          </Button>
          <Button
            size="sm"
            onClick={() => navigate(`/proposals/${id}/qc`)}
          >
            <Send className="h-4 w-4 mr-2" />
            Submeter para QC
          </Button>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden mt-4">
        {/* Left Sidebar - Sections */}
        <SectionSidebar
          sections={selectedProposal.sections}
          activeSection={activeSectionId}
          onSectionChange={handleSectionChange}
        />

        {/* Center - Editor */}
        <div className="flex-1 flex flex-col bg-card border-x border-border">
          {/* Toolbar */}
          <div className="flex items-center gap-1 p-2 border-b border-border">
            <TooltipProvider>
              {toolbarButtons.map((btn) => (
                <Tooltip key={btn.action}>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      {btn.label}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{btn.title}</p>
                  </TooltipContent>
                </Tooltip>
              ))}
            </TooltipProvider>
            <Separator orientation="vertical" className="h-6 mx-2" />
            <AIAssistButton
              section={activeSection?.title || ''}
              onApply={handleAISuggestion}
            />
          </div>

          {/* Editor Content */}
          <div className="flex-1 p-6 overflow-auto">
            <Textarea
              value={editorContent}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder={`Escreva o conteúdo para ${activeSection?.title}...`}
              className="w-full h-full min-h-[400px] resize-none border-0 focus-visible:ring-0 text-base leading-relaxed"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-3 border-t border-border">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{editorContent.length} caracteres</span>
              <span>{editorContent.split(/\s+/).filter(Boolean).length} palavras</span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                Rascunho
              </Button>
              <Button size="sm">
                <CheckCircle className="h-4 w-4 mr-2" />
                Marcar como Completo
              </Button>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Context */}
        <div className="w-80 bg-card flex flex-col overflow-auto">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Requisitos do ToR
            </h3>
          </div>
          <div className="p-4 space-y-3">
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Experiência mínima</p>
              <p className="text-xs text-muted-foreground mt-1">
                10 anos em projetos de educação
              </p>
              <Badge variant="outline" className="mt-2 text-xs">
                Obrigatório
              </Badge>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Especialista em género</p>
              <p className="text-xs text-muted-foreground mt-1">
                Experiência em inclusão social
              </p>
              <Badge variant="outline" className="mt-2 text-xs">
                Preferencial
              </Badge>
            </div>
          </div>

          <div className="p-4 border-y border-border">
            <h3 className="font-semibold flex items-center gap-2">
              <CheckSquare className="h-4 w-4" />
              Checklist
            </h3>
          </div>
          <div className="p-4 space-y-2">
            {[
              'Capa com informações corretas',
              'Resumo executivo ≤ 2 páginas',
              'Metodologia detalhada',
              'Equipa qualificada',
              'Orçamento dentro do limite',
            ].map((item, index) => (
              <label
                key={index}
                className="flex items-start gap-2 text-sm cursor-pointer"
              >
                <input type="checkbox" className="mt-0.5" />
                <span className="text-muted-foreground">{item}</span>
              </label>
            ))}
          </div>

          <div className="p-4 border-y border-border">
            <h3 className="font-semibold flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Sugestões IA
            </h3>
          </div>
          <div className="p-4 space-y-3">
            <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg">
              <p className="text-sm">
                Inclua mais detalhes sobre a abordagem de género na metodologia.
              </p>
              <Button variant="link" size="sm" className="h-auto p-0 mt-1">
                Aplicar sugestão
                <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
