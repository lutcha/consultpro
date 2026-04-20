// ============================================
// FEATURES SECTION - LANDING PAGE
// ============================================

import { FileSearch, Users, FileCheck, Sparkles, Clock, Shield } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const features = [
  {
    icon: FileSearch,
    title: 'Análise IA de ToR',
    description:
      'Extração automática de requisitos, riscos e critérios de avaliação em segundos. Nossa IA analisa documentos complexos e identifica pontos-chave.',
    color: 'text-primary',
    bgColor: 'bg-primary/10',
  },
  {
    icon: Users,
    title: 'Matching de Equipa',
    description:
      'Encontre os consultores ideais com base em skills, experiência e disponibilidade. Sistema inteligente de alocação de recursos.',
    color: 'text-accent',
    bgColor: 'bg-accent/10',
  },
  {
    icon: FileCheck,
    title: 'Quality Check Automático',
    description:
      'Validação de conformidade com ToR e critérios QCBS antes da submissão. Garanta a qualidade da sua proposta.',
    color: 'text-warning',
    bgColor: 'bg-warning/10',
  },
  {
    icon: Sparkles,
    title: 'Geração de Conteúdo IA',
    description:
      'Assistente IA para expandir, resumir e ajustar o tom do seu texto. Escreva propostas mais eficazes em menos tempo.',
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
  {
    icon: Clock,
    title: 'Gestão de Prazos',
    description:
      'Acompanhamento de deadlines com alertas inteligentes. Nunca perca uma data de submissão importante.',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
  },
  {
    icon: Shield,
    title: 'Conformidade Total',
    description:
      'Garanta que todas as exigências do ToR são cumpridas. Checklists automáticos e validação de requisitos.',
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
  },
];

export function FeaturesSection() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Tudo o que precisa para{' '}
            <span className="text-primary">ganhar mais concursos</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Uma plataforma completa que cobre todo o ciclo de vida das suas 
            propostas de consultoria internacional.
          </p>
        </div>
        
        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card
                key={feature.title}
                className="group card-hover border-border/50"
              >
                <CardHeader>
                  <div
                    className={`h-12 w-12 ${feature.bgColor} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
                  >
                    <Icon className={`h-6 w-6 ${feature.color}`} />
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
