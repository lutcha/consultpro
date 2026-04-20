// ============================================
// HOW IT WORKS SECTION - LANDING PAGE
// ============================================

import { Upload, Brain, FileCheck, ArrowRight } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: Upload,
    title: 'Upload do ToR',
    description:
      'Carregue o documento Termos de Referência em PDF ou DOCX. Nossa plataforma suporta todos os formatos principais.',
  },
  {
    number: '02',
    icon: Brain,
    title: 'Análise IA',
    description:
      'O sistema extrai automaticamente requisitos, identifica riscos e sugere a melhor estratégia para a sua proposta.',
  },
  {
    number: '03',
    icon: FileCheck,
    title: 'Proposta Pronta',
    description:
      'Gere documentos profissionais em minutos com o nosso editor colaborativo e submeta com confiança.',
  },
];

export function HowItWorksSection() {
  return (
    <section className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Como funciona a <span className="text-primary">ConsultPro</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Três passos simples para transformar a forma como cria 
            propostas de consultoria internacional.
          </p>
        </div>
        
        {/* Steps */}
        <div className="relative">
          {/* Connection line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-border -translate-y-1/2" />
          
          <div className="grid lg:grid-cols-3 gap-8 lg:gap-12">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isLast = index === steps.length - 1;
              
              return (
                <div key={step.number} className="relative">
                  <div className="bg-card rounded-2xl border border-border p-8 relative z-10">
                    {/* Step number */}
                    <div className="absolute -top-4 left-8 bg-primary text-primary-foreground text-sm font-bold px-3 py-1 rounded-full">
                      Passo {step.number}
                    </div>
                    
                    {/* Icon */}
                    <div className="h-16 w-16 bg-primary/10 rounded-xl flex items-center justify-center mb-6">
                      <Icon className="h-8 w-8 text-primary" />
                    </div>
                    
                    {/* Content */}
                    <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                    <p className="text-muted-foreground">{step.description}</p>
                  </div>
                  
                  {/* Arrow */}
                  {!isLast && (
                    <div className="hidden lg:flex absolute top-1/2 -right-6 transform -translate-y-1/2 z-20">
                      <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center shadow-lg">
                        <ArrowRight className="h-5 w-5 text-primary-foreground" />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Stats */}
        <div className="mt-20 grid grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            { value: '75%', label: 'Redução no tempo de preparação' },
            { value: '3x', label: 'Mais propostas submetidas' },
            { value: '68%', label: 'Taxa média de vitória' },
            { value: '500+', label: 'Consultores na plataforma' },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl sm:text-4xl font-bold text-primary mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
