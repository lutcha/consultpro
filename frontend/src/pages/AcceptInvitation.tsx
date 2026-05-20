// ============================================
// ACCEPT INVITATION PAGE
// ============================================

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Briefcase, Loader2, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiAcceptInvitation } from '@/lib/api';

export function AcceptInvitation() {
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    password: '',
    confirm_password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) { setError('Token inválido.'); return; }
    if (form.password !== form.confirm_password) {
      setError('As passwords não coincidem.');
      return;
    }
    if (form.password.length < 8) {
      setError('A password deve ter pelo menos 8 caracteres.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await apiAcceptInvitation({
        token,
        first_name: form.first_name,
        last_name: form.last_name,
        password: form.password,
        confirm_password: form.confirm_password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Convite inválido ou expirado.';
      setError(msg);
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
            <CardTitle className="text-2xl text-center">Ativar Conta</CardTitle>
            <CardDescription className="text-center">
              Completa o teu perfil para aceder à plataforma
            </CardDescription>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="flex flex-col items-center gap-4 py-4 text-center">
                <CheckCircle className="h-12 w-12 text-green-500" />
                <p className="font-medium">Conta ativada com sucesso!</p>
                <p className="text-sm text-muted-foreground">A redirecionar para o login...</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">Nome *</Label>
                    <Input
                      id="first_name"
                      value={form.first_name}
                      onChange={(e) => setForm(f => ({ ...f, first_name: e.target.value }))}
                      placeholder="João"
                      required
                      autoFocus
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Apelido</Label>
                    <Input
                      id="last_name"
                      value={form.last_name}
                      onChange={(e) => setForm(f => ({ ...f, last_name: e.target.value }))}
                      placeholder="Ferreira"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password *</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={form.password}
                    onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))}
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
                    onChange={(e) => setForm(f => ({ ...f, confirm_password: e.target.value }))}
                    required
                  />
                </div>

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />A ativar...</>
                  ) : (
                    'Ativar Conta'
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
