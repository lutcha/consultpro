// ============================================
// TESTIMONIALS SECTION - LANDING PAGE
// ============================================

import { Quote } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

const testimonials = [
  {
    quote:
      'A ConsultPro transformou completamente a nossa forma de trabalhar. Conseguimos reduzir o tempo de preparação de propostas em 70% e aumentar significativamente a nossa taxa de sucesso.',
    author: 'Dr. Ana Mendes',
    role: 'Diretora de Consultoria',
    company: 'Global Consulting Lda',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=AnaMendes',
  },
  {
    quote:
      'A análise IA de ToR é incrível. Consegue identificar requisitos que passariam despercebidos e ajuda-nos a criar propostas muito mais alinhadas com as expectativas dos clientes.',
    author: 'Carlos Silva',
    role: 'Senior Consultant',
    company: 'African Development Partners',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=CarlosSilva',
  },
  {
    quote:
      'O sistema de Quality Check garante que nunca submetemos uma proposta incompleta. É como ter um revisor experiente sempre disponível.',
    author: 'Maria Santos',
    role: 'Project Manager',
    company: 'EuroConsult Group',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=MariaSantos',
  },
];

export function TestimonialsSection() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            O que dizem os nossos <span className="text-primary">clientes</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Consultores e empresas de todo o mundo confiam na ConsultPro 
            para gerir as suas propostas internacionais.
          </p>
        </div>
        
        {/* Testimonials */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial) => (
            <Card
              key={testimonial.author}
              className="card-hover border-border/50"
            >
              <CardContent className="p-6">
                <Quote className="h-8 w-8 text-primary/30 mb-4" />
                <p className="text-foreground mb-6 leading-relaxed">
                  "{testimonial.quote}"
                </p>
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage
                      src={testimonial.avatar}
                      alt={testimonial.author}
                    />
                    <AvatarFallback>
                      {testimonial.author.charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-semibold text-sm">
                      {testimonial.author}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {testimonial.role}
                    </p>
                    <p className="text-xs text-primary">
                      {testimonial.company}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
