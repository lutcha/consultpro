// ============================================
// HERO SECTION - LANDING PAGE
// ============================================

import { ArrowRight, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

export function HeroSection() {
  const navigate = useNavigate();
  
  return (
    <section className="relative py-20 lg:py-32 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent/5" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Content */}
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-foreground">
                Automatize as suas{' '}
                <span className="text-primary">propostas de consultoria</span>{' '}
                internacional
              </h1>
              <p className="text-lg sm:text-xl text-muted-foreground max-w-xl">
                Plataforma inteligente que acelera a criação, revisão e submissão 
                de propostas para UN, Banco Mundial, UE e outros organismos.
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                size="lg"
                onClick={() => navigate('/dashboard')}
                className="gap-2"
              >
                Entrar na Plataforma
                <ArrowRight className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                Ver demonstração
              </Button>
            </div>
            
            {/* Trust badges */}
            <div className="pt-8 border-t border-border">
              <p className="text-sm text-muted-foreground mb-4">
                Confiam em nós consultores de:
              </p>
              <div className="flex flex-wrap gap-6 items-center opacity-60">
                <span className="text-lg font-semibold">UNICEF</span>
                <span className="text-lg font-semibold">World Bank</span>
                <span className="text-lg font-semibold">AfDB</span>
                <span className="text-lg font-semibold">EU</span>
              </div>
            </div>
          </div>
          
          {/* Illustration */}
          <div className="relative">
            <div className="aspect-square lg:aspect-[4/3] rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-accent/10 border border-border p-8 flex items-center justify-center">
              <div className="relative w-full max-w-md">
                {/* Mock dashboard preview */}
                <div className="bg-card rounded-xl shadow-lg border border-border overflow-hidden">
                  {/* Header */}
                  <div className="h-8 bg-muted border-b border-border flex items-center px-3 gap-1.5">
                    <div className="h-2.5 w-2.5 rounded-full bg-error/60" />
                    <div className="h-2.5 w-2.5 rounded-full bg-warning/60" />
                    <div className="h-2.5 w-2.5 rounded-full bg-success/60" />
                  </div>
                  {/* Content */}
                  <div className="p-4 space-y-4">
                    {/* KPI cards */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-muted rounded-lg p-2">
                        <div className="h-2 w-8 bg-muted-foreground/20 rounded mb-2" />
                        <div className="h-4 w-12 bg-primary/30 rounded" />
                      </div>
                      <div className="bg-muted rounded-lg p-2">
                        <div className="h-2 w-8 bg-muted-foreground/20 rounded mb-2" />
                        <div className="h-4 w-12 bg-accent/30 rounded" />
                      </div>
                      <div className="bg-muted rounded-lg p-2">
                        <div className="h-2 w-8 bg-muted-foreground/20 rounded mb-2" />
                        <div className="h-4 w-12 bg-warning/30 rounded" />
                      </div>
                    </div>
                    {/* Table */}
                    <div className="space-y-2">
                      <div className="h-3 w-full bg-muted-foreground/10 rounded" />
                      <div className="h-3 w-full bg-muted-foreground/10 rounded" />
                      <div className="h-3 w-3/4 bg-muted-foreground/10 rounded" />
                    </div>
                    {/* Progress */}
                    <div className="space-y-1">
                      <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                        <div className="h-full w-3/4 bg-primary rounded-full" />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Progresso</span>
                        <span>75%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Floating elements */}
                <div className="absolute -top-4 -right-4 bg-card rounded-lg shadow-lg border border-border p-3 animate-in fade-in slide-in">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 bg-success/10 rounded-full flex items-center justify-center">
                      <span className="text-success text-lg">✓</span>
                    </div>
                    <div>
                      <p className="text-xs font-medium">QC Aprovado</p>
                      <p className="text-xs text-muted-foreground">Score: 92/100</p>
                    </div>
                  </div>
                </div>
                
                <div className="absolute -bottom-4 -left-4 bg-card rounded-lg shadow-lg border border-border p-3 animate-in fade-in">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-primary text-lg">🤖</span>
                    </div>
                    <div>
                      <p className="text-xs font-medium">Análise IA</p>
                      <p className="text-xs text-muted-foreground">12 requisitos</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
