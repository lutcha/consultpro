// ============================================
// RICH TEXT EDITOR - Simple contentEditable
// ============================================

import { useRef, useEffect, useCallback } from 'react';
import { Bold, Italic, Underline, List, ListOrdered, Heading1, Heading2, Quote, Link, AlignLeft, AlignCenter, AlignRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface RichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function RichTextEditor({ value, onChange, placeholder: _placeholder, className }: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);

  // Update editor content when value prop changes (from outside)
  useEffect(() => {
    if (editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value || '';
    }
  }, []);

  const handleInput = useCallback(() => {
    if (editorRef.current) {
      onChange(editorRef.current.innerHTML);
    }
  }, [onChange]);

  const exec = useCallback((command: string, valueArg: string = '') => {
    document.execCommand(command, false, valueArg);
    if (editorRef.current) {
      editorRef.current.focus();
      handleInput();
    }
  }, [handleInput]);

  const ToolbarButton = ({
    icon: Icon,
    command,
    arg,
    title,
  }: {
    icon: React.ElementType;
    command: string;
    arg?: string;
    title: string;
  }) => (
    <Button
      variant="ghost"
      size="sm"
      className="h-8 w-8 p-0"
      onClick={(e) => {
        e.preventDefault();
        exec(command, arg || '');
      }}
      title={title}
      type="button"
    >
      <Icon className="h-4 w-4" />
    </Button>
  );

  return (
    <div className={cn('border rounded-md flex flex-col bg-card', className)}>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-0.5 p-2 border-b bg-muted/30">
        <ToolbarButton icon={Bold} command="bold" title="Negrito" />
        <ToolbarButton icon={Italic} command="italic" title="Itálico" />
        <ToolbarButton icon={Underline} command="underline" title="Sublinhado" />
        <Separator orientation="vertical" className="h-6 mx-1" />
        <ToolbarButton icon={Heading1} command="formatBlock" arg="H1" title="Título 1" />
        <ToolbarButton icon={Heading2} command="formatBlock" arg="H2" title="Título 2" />
        <Separator orientation="vertical" className="h-6 mx-1" />
        <ToolbarButton icon={List} command="insertUnorderedList" title="Lista" />
        <ToolbarButton icon={ListOrdered} command="insertOrderedList" title="Lista Numerada" />
        <Separator orientation="vertical" className="h-6 mx-1" />
        <ToolbarButton icon={AlignLeft} command="justifyLeft" title="Alinhar Esquerda" />
        <ToolbarButton icon={AlignCenter} command="justifyCenter" title="Alinhar Centro" />
        <ToolbarButton icon={AlignRight} command="justifyRight" title="Alinhar Direita" />
        <Separator orientation="vertical" className="h-6 mx-1" />
        <ToolbarButton icon={Quote} command="formatBlock" arg="BLOCKQUOTE" title="Citação" />
        <ToolbarButton
          icon={Link}
          command="createLink"
          arg="https://"
          title="Inserir Link"
        />
      </div>

      {/* Editor Area */}
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        onInput={handleInput}
        onBlur={handleInput}
        className="flex-1 p-4 min-h-[300px] outline-none prose prose-sm max-w-none dark:prose-invert"
        style={{ minHeight: '300px' }}
        dangerouslySetInnerHTML={{ __html: value || '' }}
      />
    </div>
  );
}
