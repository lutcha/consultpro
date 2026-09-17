// ============================================
// SIGN UP PAGE - Self-service (Workstream T9)
// ============================================

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Loader2, MailCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiSelfSignup } from '@/lib/api';

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined;

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: Record<string, unknown>) => string;
      reset: (widgetId?: string) => void;
    };
  }
}

function useTurnstile(onToken: (token: string) => void) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);

  useEffect(() => {
    if (!TURNSTILE_SITE_KEY) return;

    const renderWidget = () => {
      if (!containerRef.current || !window.turnstile || widgetId.current) return;
      widgetId.current = window.turnstile.render(containerRef.current, {
        sitekey: TURNSTILE_SITE_KEY,
        callback: onToken,
      });
    };

    if (window.turnstile) {
      renderWidget();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
    script.async = true;
    script.defer = true;
    script.onload = renderWidget;
    document.head.appendChild(script);

    return () => {
      script.onload = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return containerRef;
}

export function SignUp() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    organization_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [turnstileToken, setTurnstileToken] = useState('');
  const turnstileRef = useTurnstile(setTurnstileToken);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      setError('As passwords não coincidem.');
      return;
    }
    if (form.password.length < 8) {
      setError('A password deve ter pelo menos 8 caracteres.');
      return;
    }
    if (TURNSTILE_SITE_KEY && !turnstileToken) {
      setError('Confirma que não és um robô.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await apiSelfSignup({ ...form, turnstile_token: turnstileToken });
      setSuccess(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Não foi possível criar a conta.';
      setError(msg);
      if (window.turnstile && turnstileRef.current) {
        window.turnstile.reset();
        setTurnstileToken('');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/50 px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="h-10 w-10 bg-primary rounded-lg flex items-center justify-center">
            <Briefcase className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="font-semibold text-xl">ConsultPro</span>
        </div>

        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Criar Conta</CardTitle>
            <CardDescription className="text-center">
              15 dias grátis. Sem cartão de crédito.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="flex flex-col items-center gap-4 py-4 text-center">
                <MailCheck className="h-12 w-12 text-green-500" />
                <p className="font-medium">Verifica o teu email</p>
                <p className="text-sm text-muted-foreground">
                  Enviámos um link de confirmação para <strong>{form.email}</strong>. Clica no link
                  para ativar a conta e começar o onboarding.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="organization_name">Nome da organização *</Label>
                  <Input
                    id="organization_name"
                    value={form.organization_name}
                    onChange={(e) => setForm((f) => ({ ...f, organization_name: e.target.value }))}
                    placeholder="Consultora Exemplo Lda"
                    required
                    autoFocus
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    placeholder="maria@exemplo.cv"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password *</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={form.password}
                    onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirmar Password *</Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    placeholder="••••••••"
                    value={form.confirm_password}
                    onChange={(e) => setForm((f) => ({ ...f, confirm_password: e.target.value }))}
                    required
                  />
                </div>

                {TURNSTILE_SITE_KEY && <div ref={turnstileRef} />}

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />A criar conta...</>
                  ) : (
                    'Criar Conta Grátis'
                  )}
                </Button>

                <p className="text-center text-sm text-muted-foreground">
                  Já tens conta?{' '}
                  <button
                    type="button"
                    className="text-primary underline-offset-4 hover:underline"
                    onClick={() => navigate('/login')}
                  >
                    Iniciar sessão
                  </button>
                </p>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
