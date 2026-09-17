// ============================================
// LEGAL PAGE LAYOUT — shared wrapper for Terms/Privacy
// Both pages are DRAFTS pending legal review — do not remove the banner
// below without confirming the content has been formally reviewed.
// ============================================

import { Link } from 'react-router-dom';
import { Briefcase, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface LegalPageLayoutProps {
  title: string;
  children: React.ReactNode;
}

export function LegalPageLayout({ title, children }: LegalPageLayoutProps) {
  return (
    <div className="min-h-screen bg-muted/30">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Link to="/" className="flex items-center gap-2 mb-8 w-fit">
          <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
            <Briefcase className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="font-semibold text-lg">ConsultPro</span>
        </Link>

        <Alert className="mb-8 border-amber-500/50 bg-amber-50 text-amber-900">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle>Rascunho — pendente de revisão legal</AlertTitle>
          <AlertDescription>
            Este documento é um rascunho gerado como ponto de partida e ainda não foi
            revisto por um profissional com competência legal. Não deve ser tratado como
            vinculativo até essa revisão ser concluída.
          </AlertDescription>
        </Alert>

        <article className="prose prose-sm sm:prose-base max-w-none prose-headings:font-semibold prose-h2:text-lg prose-h2:mt-8 prose-h2:mb-3 prose-p:text-muted-foreground prose-li:text-muted-foreground">
          <h1 className="text-2xl font-bold mb-2">{title}</h1>
          <p className="text-sm text-muted-foreground mb-8">
            Última atualização: {new Date().toLocaleDateString('pt-PT', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
          {children}
        </article>
      </div>
    </div>
  );
}
