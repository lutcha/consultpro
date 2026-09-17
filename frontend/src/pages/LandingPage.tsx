// ============================================
// LANDING PAGE
// ============================================

import { useNavigate } from 'react-router-dom';
import { Briefcase, Menu, X, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import { HeroSection } from '@/components/landing/HeroSection';
import { FeaturesSection } from '@/components/landing/FeaturesSection';
import { HowItWorksSection } from '@/components/landing/HowItWorksSection';
import { TestimonialsSection } from '@/components/landing/TestimonialsSection';
import { Footer } from '@/components/layout/Footer';

const navLinks = [
  { label: 'Funcionalidades', href: '#features' },
  { label: 'Como Funciona', href: '#how-it-works' },
  { label: 'Planos', href: '#plans' },
  { label: 'Contacto', href: 'mailto:info@consultpro.cv' },
];

const plans = [
  {
    name: 'Beta',
    price: 'Gratuito',
    period: 'acesso limitado',
    description: 'Para organizações seleccionadas no programa beta assistido.',
    features: [
      'Até 50 oportunidades/mês',
      'World Bank + ECREEE incluídos',
      'Proposta + QC + Export light',
      'Onboarding assistido',
      '1 organização',
    ],
    cta: 'Criar Conta Grátis',
    highlight: false,
    plan: 'beta',
    ctaTarget: 'signup' as const,
  },
  {
    name: 'Profissional',
    price: 'Em breve',
    period: '',
    description: 'Para equipas que precisam de inteligência comercial completa.',
    features: [
      'Oportunidades ilimitadas',
      'Todas as fontes de scraping',
      'AI scoring + Go/No-Go',
      'Export completo PDF/PPT',
      'Partner matching',
      'Analytics avançados',
    ],
    cta: 'Criar Conta Grátis',
    highlight: true,
    plan: 'pro',
    ctaTarget: 'signup' as const,
  },
  {
    name: 'Enterprise',
    price: 'A definir',
    period: '',
    description: 'Para grupos e firmas com múltiplas unidades de negócio.',
    features: [
      'Multi-tenant / Multi-org',
      'SSO / OIDC',
      'RLS e isolamento de dados',
      'Fontes proprietárias',
      'SLA dedicado',
      'Onboarding white-glove',
    ],
    cta: 'Falar com Equipa',
    highlight: false,
    plan: 'enterprise',
    ctaTarget: 'mailto' as const,
  },
];

function SignupCta() {
  const navigate = useNavigate();
  return (
    <section className="py-20 bg-primary">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold text-primary-foreground mb-4">
          Comece agora — 15 dias grátis
        </h2>
        <p className="text-lg text-primary-foreground/80 mb-8">
          Cria a tua conta em minutos. Sem cartão de crédito, sem espera por aprovação manual.
        </p>
        <Button size="lg" variant="secondary" onClick={() => navigate('/signup')}>
          Criar Conta Grátis
        </Button>
        <p className="text-sm text-primary-foreground/60 mt-4">
          Precisas de SSO, RLS dedicado ou onboarding white-glove?{' '}
          <a href="mailto:info@consultpro.cv" className="underline">Fala com a equipa</a>.
        </p>
      </div>
    </section>
  );
}

export function LandingPage() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-lg">ConsultPro</span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            {/* CTA Buttons */}
            <div className="hidden md:flex items-center gap-4">
              <Button variant="ghost" onClick={() => navigate('/login')}>
                Entrar
              </Button>
              <Button onClick={() => navigate('/signup')}>
                Criar Conta
              </Button>
            </div>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border">
            <div className="px-4 py-4 space-y-4">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="block text-sm font-medium text-muted-foreground hover:text-foreground"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </a>
              ))}
              <div className="pt-4 border-t border-border space-y-2">
                <Button variant="outline" className="w-full" onClick={() => navigate('/login')}>
                  Entrar
                </Button>
                <Button className="w-full" onClick={() => { setMobileMenuOpen(false); navigate('/signup'); }}>
                  Criar Conta
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main>
        <HeroSection />
        <div id="features">
          <FeaturesSection />
        </div>
        <div id="how-it-works">
          <HowItWorksSection />
        </div>
        <div id="testimonials">
          <TestimonialsSection />
        </div>

        {/* Pricing Section */}
        <section id="plans" className="py-20 bg-muted/30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">Planos simples e transparentes</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Comece com o beta assistido e escale quando estiver pronto. Sem surpresas.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {plans.map((plan) => (
                <div
                  key={plan.name}
                  className={`rounded-2xl border p-8 flex flex-col gap-6 ${plan.highlight ? 'border-primary bg-primary/5 shadow-lg' : 'bg-background'}`}
                >
                  <div>
                    {plan.highlight && (
                      <span className="text-xs font-semibold text-primary uppercase tracking-wide mb-2 block">Mais Popular</span>
                    )}
                    <h3 className="text-xl font-bold">{plan.name}</h3>
                    <div className="mt-2 flex items-baseline gap-1">
                      <span className="text-3xl font-bold">{plan.price}</span>
                      {plan.period && <span className="text-sm text-muted-foreground">· {plan.period}</span>}
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
                  </div>
                  <ul className="space-y-2 flex-1">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm">
                        <Check className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant={plan.highlight ? 'default' : 'outline'}
                    className="w-full"
                    onClick={() =>
                      plan.ctaTarget === 'mailto'
                        ? (window.location.href = 'mailto:info@consultpro.cv')
                        : navigate('/signup')
                    }
                  >
                    {plan.cta}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Signup CTA */}
        <SignupCta />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
