// ============================================
// LANDING PAGE
// ============================================

import { useNavigate } from 'react-router-dom';
import { Briefcase, Menu, X, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
  { label: 'Contacto', href: '#contact' },
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
    cta: 'Solicitar Acesso Beta',
    highlight: false,
    plan: 'beta',
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
    cta: 'Manifestar Interesse',
    highlight: true,
    plan: 'pro',
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
  },
];

function BetaAccessForm() {
  const [form, setForm] = useState({ name: '', organization: '', email: '', plan: 'beta', message: '' });
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

  const update = (key: keyof typeof form, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('sending');
    try {
      const res = await fetch('/api/beta-access/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      setStatus(res.ok ? 'sent' : 'error');
    } catch {
      setStatus('error');
    }
  };

  return (
    <section id="contact" className="py-20 bg-primary">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-bold text-primary-foreground mb-4">
            Solicitar Acesso Beta
          </h2>
          <p className="text-lg text-primary-foreground/80">
            O beta é assistido e por convite. Preencha o formulário e entraremos em contacto em 24h.
          </p>
        </div>

        {status === 'sent' ? (
          <div className="bg-primary-foreground/10 rounded-2xl p-8 text-center text-primary-foreground">
            <Check className="h-10 w-10 mx-auto mb-4" />
            <p className="text-lg font-semibold">Pedido recebido!</p>
            <p className="text-primary-foreground/80 mt-2">Vamos entrar em contacto em breve para agendar o onboarding.</p>
          </div>
        ) : (
          <form onSubmit={submit} className="bg-primary-foreground/10 rounded-2xl p-8 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-primary-foreground/90">Nome *</Label>
                <Input value={form.name} onChange={(e) => update('name', e.target.value)} required placeholder="Maria Silva" className="bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground placeholder:text-primary-foreground/40" />
              </div>
              <div className="space-y-1">
                <Label className="text-primary-foreground/90">Organização</Label>
                <Input value={form.organization} onChange={(e) => update('organization', e.target.value)} placeholder="Consultora Exemplo Lda" className="bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground placeholder:text-primary-foreground/40" />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-primary-foreground/90">Email *</Label>
              <Input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} required placeholder="maria@exemplo.cv" className="bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground placeholder:text-primary-foreground/40" />
            </div>
            <div className="space-y-1">
              <Label className="text-primary-foreground/90" htmlFor="plan-select">Plano de interesse</Label>
              <select
                id="plan-select"
                value={form.plan}
                onChange={(e) => update('plan', e.target.value)}
                className="w-full h-10 rounded-md border border-primary-foreground/20 bg-primary-foreground/10 px-3 text-sm text-primary-foreground"
              >
                <option value="beta">Beta (gratuito)</option>
                <option value="pro">Profissional</option>
                <option value="enterprise">Enterprise</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label className="text-primary-foreground/90">O que procura melhorar?</Label>
              <Textarea value={form.message} onChange={(e) => update('message', e.target.value)} rows={3} placeholder="Ex: Identificar oportunidades no Banco Mundial, melhorar a qualidade das propostas..." className="bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground placeholder:text-primary-foreground/40" />
            </div>
            {status === 'error' && (
              <p className="text-sm text-red-300">Erro ao enviar. Tente novamente ou escreva para <a href="mailto:info@consultpro.cv" className="underline">info@consultpro.cv</a>.</p>
            )}
            <Button type="submit" size="lg" variant="secondary" className="w-full" disabled={status === 'sending'}>
              {status === 'sending' ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />A enviar...</> : 'Enviar Pedido'}
            </Button>
          </form>
        )}
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
              <Button onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}>
                Solicitar Acesso
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
                <Button className="w-full" onClick={() => { setMobileMenuOpen(false); document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' }); }}>
                  Solicitar Acesso
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
                    onClick={() => {
                      const el = document.getElementById('contact');
                      if (el) el.scrollIntoView({ behavior: 'smooth' });
                      setTimeout(() => {
                        const planInput = document.getElementById('plan-select') as HTMLSelectElement | null;
                        if (planInput) planInput.value = plan.plan;
                      }, 400);
                    }}
                  >
                    {plan.cta}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Beta Access Form */}
        <BetaAccessForm />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
