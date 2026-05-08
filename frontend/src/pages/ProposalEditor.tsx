// ============================================
// PROPOSAL EDITOR PAGE - Rich Text + Word/PDF Export
// ============================================

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Send,
  CheckCircle,
  ChevronRight,
  FileText,
  CheckSquare,
  Lightbulb,
  FileType,
  FileDown,
  Upload,
  Building2,
  UserCircle,
  Plus,
  X,
  Eye,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AIAssistButton } from '@/components/proposals/AIAssistButton';
import { RichTextEditor } from '@/components/proposals/RichTextEditor';
import { useProposalStore } from '@/stores';
import {
  apiDownloadProposalWord,
  apiDownloadProposalPdf,
  apiCreateProposalSection,
  apiGenerateProposalSectionSuggestion,
  apiUploadProposalLogo,
} from '@/lib/api';

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatInlineMarkdown(value: string) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>');
}

function isMarkdownTableSeparator(line: string) {
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim());
}

function hasMarkdownTableCells(line: string) {
  return splitMarkdownTableRow(line).length >= 3;
}

function splitMarkdownTableRow(line: string) {
  return line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim());
}

function renderMarkdownTable(rows: string[]) {
  if (rows.length < 2) {
    return '';
  }

  const headers = splitMarkdownTableRow(rows[0]);
  const hasSeparator = isMarkdownTableSeparator(rows[1]);
  const bodyRows = rows.slice(hasSeparator ? 2 : 1).map(splitMarkdownTableRow);
  const headerHtml = headers
    .map((header) => `<th>${formatInlineMarkdown(header)}</th>`)
    .join('');
  const bodyHtml = bodyRows
    .map((row) => {
      const cells = headers.map((_, index) => row[index] || '');
      return `<tr>${cells
        .map((cell) => `<td>${formatInlineMarkdown(cell)}</td>`)
        .join('')}</tr>`;
    })
    .join('');

  return `<table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table>`;
}

function normalizeAiMarkdown(markdown: string) {
  return markdown
    .replace(/&lt;br\s*\/?&gt;/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>\s*<p>/gi, '\n\n')
    .replace(/<\/?(p|div|span)>/gi, '')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>');
}

function aiMarkdownToHtml(markdown: string) {
  const lines = normalizeAiMarkdown(markdown)
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .split('\n');
  const html: string[] = [];
  let listType: 'ul' | 'ol' | null = null;

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`);
      listType = null;
    }
  };

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index];
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }

    const nextLine = lines[index + 1]?.trim() || '';
    if (
      hasMarkdownTableCells(line) &&
      (isMarkdownTableSeparator(nextLine) || hasMarkdownTableCells(nextLine))
    ) {
      closeList();
      const tableRows = [line];
      index += 1;
      while (index < lines.length && hasMarkdownTableCells(lines[index].trim())) {
        tableRows.push(lines[index].trim());
        index += 1;
      }
      index -= 1;
      html.push(renderMarkdownTable(tableRows));
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      closeList();
      const level = heading[1].length + 1;
      html.push(`<h${level}>${formatInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    const bullet = line.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (listType !== 'ul') {
        closeList();
        html.push('<ul>');
        listType = 'ul';
      }
      html.push(`<li>${formatInlineMarkdown(bullet[1])}</li>`);
      continue;
    }

    const numbered = line.match(/^\d+[.)]\s+(.+)$/);
    if (numbered) {
      if (listType !== 'ol') {
        closeList();
        html.push('<ol>');
        listType = 'ol';
      }
      html.push(`<li>${formatInlineMarkdown(numbered[1])}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${formatInlineMarkdown(line)}</p>`);
  }

  closeList();
  return html.join('');
}

export function ProposalEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedProposal, selectProposal, updateSection, autoSaveStatus } =
    useProposalStore();
  const [activeSectionId, setActiveSectionId] = useState<string>('');
  const [editorContent, setEditorContent] = useState('');
  const [isExporting, setIsExporting] = useState<'word' | 'pdf' | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [consortiumMembers, setConsortiumMembers] = useState<string[]>([]);
  const [newMember, setNewMember] = useState('');
  const [newSectionTitle, setNewSectionTitle] = useState('');
  const [isAddingSection, setIsAddingSection] = useState(false);
  const [logos, setLogos] = useState<{
    proponent?: string;
    client?: string;
  }>({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadType, setUploadType] = useState<'proponent' | 'client'>('proponent');
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (id) {
      selectProposal(id);
    }
  }, [id, selectProposal]);

  useEffect(() => {
    if (selectedProposal) {
      setConsortiumMembers(selectedProposal.consortiumMembers || []);
      setLogos({
        proponent: selectedProposal.proponentLogoUrl || undefined,
        client: selectedProposal.clientLogoUrl || undefined,
      });
      if (selectedProposal.sections.length > 0 && !activeSectionId) {
        setActiveSectionId(selectedProposal.sections[0].id);
      }
    }
  }, [selectedProposal]);

  useEffect(() => {
    if (selectedProposal && activeSectionId) {
      const section = selectedProposal.sections.find((s) => s.id === activeSectionId);
      if (section) {
        setEditorContent(section.content || '');
      }
    }
  }, [selectedProposal, activeSectionId]);

  const saveSection = useCallback(
    (content: string) => {
      if (selectedProposal && activeSectionId) {
        updateSection(selectedProposal.id, activeSectionId, content);
      }
    },
    [selectedProposal, activeSectionId, updateSection]
  );

  const handleContentChange = (content: string) => {
    setEditorContent(content);
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      saveSection(content);
    }, 1500);
  };

  const handleSectionChange = (sectionId: string) => {
    if (activeSectionId && editorContent) {
      saveSection(editorContent);
    }
    setActiveSectionId(sectionId);
  };

  const handleExport = async (type: 'word' | 'pdf') => {
    if (!id) return;
    setIsExporting(type);
    try {
      const blob = type === 'word'
        ? await apiDownloadProposalWord(id)
        : await apiDownloadProposalPdf(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Proposta_${id}_${selectedProposal?.title?.replace(/\s+/g, '_') || 'document'}.${type === 'word' ? 'docx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao exportar');
    } finally {
      setIsExporting(null);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    try {
      const result = await apiUploadProposalLogo(id, file, uploadType);
      setLogos((prev) => ({ ...prev, [uploadType]: result.url }));
    } catch (err) {
      alert('Erro ao fazer upload do logo');
    }
  };

  const triggerUpload = (type: 'proponent' | 'client') => {
    setUploadType(type);
    fileInputRef.current?.click();
  };

  const handleAddConsortiumMember = () => {
    if (newMember.trim()) {
      setConsortiumMembers((prev) => [...prev, newMember.trim()]);
      setNewMember('');
    }
  };

  const handleRemoveConsortiumMember = (index: number) => {
    setConsortiumMembers((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddSection = async () => {
    if (!selectedProposal || !newSectionTitle.trim() || isAddingSection) return;
    setIsAddingSection(true);
    try {
      const section = await apiCreateProposalSection(selectedProposal.id, {
        title: newSectionTitle.trim(),
      });
      setNewSectionTitle('');
      await selectProposal(selectedProposal.id);
      setActiveSectionId(String(section.id));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao criar secao');
    } finally {
      setIsAddingSection(false);
    }
  };

  const handleAISuggestion = async (action: string) => {
    if (!selectedProposal || !activeSectionId) return;
    try {
      const suggestion = await apiGenerateProposalSectionSuggestion(selectedProposal.id, {
        section_id: activeSectionId,
        action,
        current_content: editorContent,
      });
      if (!suggestion.generated_content) {
        alert('A IA nao devolveu conteudo para esta secao.');
        return;
      }

      const generatedContent = aiMarkdownToHtml(suggestion.generated_content);
      const shouldAppend = action === 'draft_from_context' && editorContent.trim();
      const nextContent = shouldAppend
        ? `${editorContent}<p><br></p>${generatedContent}`
        : generatedContent;

      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
      setEditorContent(nextContent);
      await updateSection(selectedProposal.id, activeSectionId, nextContent);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao gerar sugestao IA');
    }
  };
  const activeSection = selectedProposal?.sections.find(
    (s) => s.id === activeSectionId
  );

  // Build preview HTML
  const previewHtml = selectedProposal
    ? `
    <div style="font-family: Calibri, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 2px solid #1A365D; padding-bottom: 20px;">
        <div style="text-align: left;">
          ${logos.proponent ? `<img src="${logos.proponent}" style="max-height: 60px; max-width: 150px;" />` : '<div style="color: #999; font-style: italic; font-size: 12px;">[LOGO EMPRESA PROPONENTE]</div>'}
        </div>
        <div style="text-align: right;">
          ${logos.client ? `<img src="${logos.client}" style="max-height: 60px; max-width: 150px;" />` : '<div style="color: #999; font-style: italic; font-size: 12px;">[LOGO CLIENTE]</div>'}
        </div>
      </div>
      
      <h1 style="color: #1A365D; font-size: 24px; text-align: center; margin-bottom: 20px;">${selectedProposal.title}</h1>
      
      <p style="text-align: center; color: #666;"><em>ID Oportunidade: ${selectedProposal.opportunityId}</em></p>
      
      ${consortiumMembers.length > 0 ? `
        <div style="margin: 30px 0; padding: 15px; background: #F7FAFC; border-radius: 8px;">
          <h3 style="color: #1A365D; margin-bottom: 10px;">Membros do Consórcio</h3>
          <ul style="margin: 0; padding-left: 20px;">
            ${consortiumMembers.map(m => `<li>${m}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      
      <hr style="margin: 30px 0; border: none; border-top: 1px solid #E2E8F0;" />
      
      ${selectedProposal.sections.map(s => `
        <div style="margin-bottom: 30px;">
          <h2 style="color: #1A365D; font-size: 18px; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">${s.title}</h2>
          <div style="line-height: 1.6; color: #333;">${s.content || '<em style="color: #999;">[Conteúdo em desenvolvimento...]</em>'}</div>
        </div>
      `).join('')}
      
      <div style="margin-top: 60px; text-align: center; color: #666; font-size: 10px; border-top: 1px solid #E2E8F0; padding-top: 20px;">
        Documento gerado automaticamente pela plataforma ConsultPro — ${new Date().getFullYear()}
      </div>
    </div>
  `
    : '';

  if (!selectedProposal) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Proposta não encontrada.</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/proposals')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Hidden file input for logo upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleLogoUpload}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/proposals')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-xl font-bold">{selectedProposal.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">v{selectedProposal.version}</Badge>
              <Badge
                variant={autoSaveStatus === 'saved' ? 'default' : 'secondary'}
                className="text-xs"
              >
                {autoSaveStatus === 'saving' && 'A guardar...'}
                {autoSaveStatus === 'saved' && 'Guardado'}
                {autoSaveStatus === 'idle' && 'Rascunho'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => setPreviewOpen(true)}>
            <Eye className="h-4 w-4 mr-2" />
            Pré-visualizar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('word')}
            disabled={isExporting !== null}
          >
            <FileType className="h-4 w-4 mr-2" />
            {isExporting === 'word' ? 'A gerar...' : 'Word'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('pdf')}
            disabled={isExporting !== null}
          >
            <FileDown className="h-4 w-4 mr-2" />
            {isExporting === 'pdf' ? 'A gerar...' : 'PDF'}
          </Button>
          <Button size="sm" onClick={() => navigate(`/proposals/${id}/qc`)}>
            <Send className="h-4 w-4 mr-2" />
            Submeter para QC
          </Button>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden mt-4">
        {/* Left Sidebar - Sections & Logos */}
        <div className="w-64 flex-shrink-0 flex flex-col border-r border-border overflow-auto">
          {/* Logos Section */}
          <div className="p-3 border-b border-border">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Logos da Proposta
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => triggerUpload('proponent')}
                className="w-full flex items-center gap-2 p-2 rounded-lg border border-dashed border-border hover:bg-muted transition-colors text-left"
              >
                {logos.proponent ? (
                  <img src={logos.proponent} alt="Proponent" className="h-8 w-8 object-contain" />
                ) : (
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                )}
                <span className="text-xs text-muted-foreground truncate">
                  {logos.proponent ? 'Logo Proponente' : 'Logo Proponente'}
                </span>
                <Upload className="h-3 w-3 ml-auto text-muted-foreground" />
              </button>
              <button
                onClick={() => triggerUpload('client')}
                className="w-full flex items-center gap-2 p-2 rounded-lg border border-dashed border-border hover:bg-muted transition-colors text-left"
              >
                {logos.client ? (
                  <img src={logos.client} alt="Client" className="h-8 w-8 object-contain" />
                ) : (
                  <UserCircle className="h-4 w-4 text-muted-foreground" />
                )}
                <span className="text-xs text-muted-foreground truncate">
                  {logos.client ? 'Logo Cliente' : 'Logo Cliente'}
                </span>
                <Upload className="h-3 w-3 ml-auto text-muted-foreground" />
              </button>
            </div>
          </div>

          {/* Consortium Members */}
          <div className="p-3 border-b border-border">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Consórcio
            </h3>
            <div className="space-y-1">
              {consortiumMembers.map((member, idx) => (
                <div key={idx} className="flex items-center gap-1 text-xs">
                  <span className="flex-1 truncate">{member}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-5 w-5 p-0"
                    onClick={() => handleRemoveConsortiumMember(idx)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
              <div className="flex gap-1 mt-2">
                <Input
                  value={newMember}
                  onChange={(e) => setNewMember(e.target.value)}
                  placeholder="Nova empresa"
                  className="h-7 text-xs"
                  onKeyDown={(e) => e.key === 'Enter' && handleAddConsortiumMember()}
                />
                <Button size="sm" className="h-7 px-2" onClick={handleAddConsortiumMember}>
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>

          {/* Sections */}
          <div className="flex-1 p-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Secções
            </h3>
            <div className="flex gap-1 mb-3">
              <Input
                value={newSectionTitle}
                onChange={(e) => setNewSectionTitle(e.target.value)}
                placeholder="Nova secao"
                className="h-7 text-xs"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSection();
                  }
                }}
              />
              <Button
                size="sm"
                className="h-7 px-2"
                onClick={handleAddSection}
                disabled={isAddingSection || !newSectionTitle.trim()}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
            <div className="space-y-1">
              {selectedProposal.sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => handleSectionChange(section.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeSectionId === section.id
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'hover:bg-muted text-muted-foreground'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {section.isComplete ? (
                      <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <div className="h-3.5 w-3.5 rounded-full border border-muted-foreground" />
                    )}
                    <span className="truncate">{section.title}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Center - Editor */}
        <div className="flex-1 flex flex-col bg-card border-x border-border overflow-hidden">
          <div className="flex items-center justify-between p-3 border-b border-border">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{activeSection?.title}</span>
              {activeSection?.isComplete && (
                <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                  Completo
                </Badge>
              )}
            </div>
            <AIAssistButton
              section={activeSection?.title || ''}
              onApply={handleAISuggestion}
            />
          </div>

          <div className="flex-1 overflow-auto p-4">
            <RichTextEditor
              value={editorContent}
              onChange={handleContentChange}
              placeholder={`Escreva o conteúdo para ${activeSection?.title}...`}
              className="h-full"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-3 border-t border-border bg-muted/30">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{editorContent.replace(/<[^>]*>/g, '').length} caracteres</span>
              <span>{editorContent.replace(/<[^>]*>/g, '').split(/\s+/).filter(Boolean).length} palavras</span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => saveSection(editorContent)}>
                <Save className="h-4 w-4 mr-2" />
                Guardar
              </Button>
              <Button size="sm" onClick={() => {
                if (activeSection) {
                  updateSection(selectedProposal.id, activeSectionId, editorContent, true);
                }
              }} disabled={activeSection?.isComplete}>
                <CheckCircle className="h-4 w-4 mr-2" />
                {activeSection?.isComplete ? 'Completo' : 'Marcar como Completo'}
              </Button>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Context */}
        <div className="w-72 flex-shrink-0 bg-card flex flex-col overflow-auto border-l border-border">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold flex items-center gap-2 text-sm">
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
            <h3 className="font-semibold flex items-center gap-2 text-sm">
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
              <label key={index} className="flex items-start gap-2 text-sm cursor-pointer">
                <input type="checkbox" className="mt-0.5" />
                <span className="text-muted-foreground">{item}</span>
              </label>
            ))}
          </div>

          <div className="p-4 border-y border-border">
            <h3 className="font-semibold flex items-center gap-2 text-sm">
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

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Pré-visualização da Proposta</DialogTitle>
          </DialogHeader>
          <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
