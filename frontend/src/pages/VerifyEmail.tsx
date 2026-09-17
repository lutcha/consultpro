// ============================================
// VERIFY EMAIL PAGE - Self-service (Workstream T9)
// ============================================

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Briefcase, Loader2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { apiVerifyEmail } from '@/lib/api';
import { useUserStore } from '@/stores';

export function VerifyEmail() {
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();
  const fetchMe = useUserStore((s) => s.fetchMe);
  const [status, setStatus] = useState<'verifying' | 'error'>('verifying');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('Link de confirmação inválido.');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await apiVerifyEmail(token);
        await fetchMe();
        if (!cancelled) navigate('/tenant-onboarding', { replace: true });
      } catch (err: unknown) {
        if (cancelled) return;
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Link de confirmação inválido ou expirado.');
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

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
            <CardTitle className="text-2xl text-center">Confirmar Email</CardTitle>
            <CardDescription className="text-center">
              A ativar a tua conta e organização
            </CardDescription>
          </CardHeader>
          <CardContent>
            {status === 'verifying' ? (
              <div className="flex flex-col items-center gap-4 py-4 text-center">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Um momento...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4 py-4 text-center">
                <XCircle className="h-12 w-12 text-destructive" />
                <p className="font-medium">Não foi possível confirmar o email</p>
                <p className="text-sm text-muted-foreground">{error}</p>
                <Button variant="outline" onClick={() => navigate('/signup')}>
                  Voltar ao registo
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
