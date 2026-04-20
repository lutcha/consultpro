// ============================================
// NEW PROJECT PAGE
// ============================================

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Briefcase } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiCreateProject } from '@/lib/api';
import { apiGetProposals } from '@/lib/api';
import type { ApiProposalListItem } from '@/lib/api';

const RISK_LEVELS = [
  { value: 'low', label: 'Baixo' },
  { value: 'medium', label: 'Médio' },
  { value: 'high', label: 'Alto' },
  { value: 'critical', label: 'Crítico' },
];

export function NewProject() {
  const navigate = useNavigate();
  const [proposals, setProposals] = useState<ApiProposalListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    proposal_id: '',
    client: '',
    client_contact_name: '',
    client_contact_email: '',
    description: '',
    sector: '',
    country: '',
    budget_total: '',
    budget_currency: 'USD',
    start_date: '',
    end_date: '',
    risk_level: 'low',
  });

  useEffect(() => {
    apiGetProposals().then((res) => {
      // Filter won proposals - for now show all since we don't have won status yet
      setProposals(res.results);
    });
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const project = await apiCreateProject({
        ...formData,
        budget_total: formData.budget_total,
        status: 'planning',
      });
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar projeto');
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/projects')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <h1 className="text-2xl font-bold">Novo Projeto</h1>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-5 w-5" />
              Informações do Projeto
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Proposta Original (opcional)</Label>
              <Select
                value={formData.proposal_id}
                onValueChange={(v) =>
                  setFormData((prev) => ({ ...prev, proposal_id: v }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecionar proposta ganha" />
                </SelectTrigger>
                <SelectContent>
                  {proposals.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {p.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">Título do Projeto *</Label>
              <Input
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="Ex: Implementação do Programa de Educação Rural"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="client">Cliente *</Label>
                <Input
                  id="client"
                  name="client"
                  value={formData.client}
                  onChange={handleChange}
                  placeholder="Ex: UNICEF"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="client_contact_name">Contacto do Cliente</Label>
                <Input
                  id="client_contact_name"
                  name="client_contact_name"
                  value={formData.client_contact_name}
                  onChange={handleChange}
                  placeholder="Nome do contacto"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="client_contact_email">Email do Contacto</Label>
              <Input
                id="client_contact_email"
                name="client_contact_email"
                type="email"
                value={formData.client_contact_email}
                onChange={handleChange}
                placeholder="contacto@cliente.com"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sector">Setor</Label>
                <Input
                  id="sector"
                  name="sector"
                  value={formData.sector}
                  onChange={handleChange}
                  placeholder="Ex: Educação"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">País</Label>
                <Input
                  id="country"
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  placeholder="Ex: Moçambique"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="budget_total">Orçamento Total *</Label>
                <Input
                  id="budget_total"
                  name="budget_total"
                  type="number"
                  value={formData.budget_total}
                  onChange={handleChange}
                  placeholder="450000"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Moeda</Label>
                <Select
                  value={formData.budget_currency}
                  onValueChange={(v) =>
                    setFormData((prev) => ({ ...prev, budget_currency: v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="risk_level">Nível de Risco</Label>
                <Select
                  value={formData.risk_level}
                  onValueChange={(v) =>
                    setFormData((prev) => ({ ...prev, risk_level: v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RISK_LEVELS.map((r) => (
                      <SelectItem key={r.value} value={r.value}>
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_date">Data de Início</Label>
                <Input
                  id="start_date"
                  name="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_date">Data de Fim</Label>
                <Input
                  id="end_date"
                  name="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descrição</Label>
              <Textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Descrição do projeto, objetivos, escopo..."
                rows={4}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            variant="outline"
            type="button"
            onClick={() => navigate('/projects')}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            <Save className="h-4 w-4 mr-2" />
            {isLoading ? 'A criar...' : 'Criar Projeto'}
          </Button>
        </div>
      </form>
    </div>
  );
}
