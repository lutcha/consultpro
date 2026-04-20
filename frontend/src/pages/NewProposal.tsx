// ============================================
// NEW PROPOSAL PAGE
// ============================================

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Save, FileText } from 'lucide-react';
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
import { useOpportunityStore } from '@/stores';
import { apiCreateProposal } from '@/lib/api';

export function NewProposal() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedOpportunityId = searchParams.get('opportunity');
  const { opportunities, fetchOpportunities } = useOpportunityStore();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    opportunity: preselectedOpportunityId || '',
    version: 1,
    description: '',
  });

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.opportunity) {
      setError('Selecione uma oportunidade');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const proposal = await apiCreateProposal({
        title: formData.title,
        opportunity: parseInt(formData.opportunity),
        version: formData.version,
        status: 'draft',
      });
      navigate(`/proposals/${proposal.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar proposta');
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/proposals')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <h1 className="text-2xl font-bold">Nova Proposta</h1>
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
              <FileText className="h-5 w-5" />
              Informações da Proposta
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="opportunity">Oportunidade *</Label>
              <Select
                value={formData.opportunity}
                onValueChange={(v) =>
                  setFormData((prev) => ({ ...prev, opportunity: v }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecionar oportunidade" />
                </SelectTrigger>
                <SelectContent>
                  {opportunities.map((opp) => (
                    <SelectItem key={opp.id} value={opp.id}>
                      {opp.title} ({opp.client})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="title">Título da Proposta *</Label>
              <Input
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="Ex: Proposta de Consultoria - Avaliação de Impacto"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="version">Versão</Label>
              <Input
                id="version"
                name="version"
                type="number"
                min={1}
                value={formData.version}
                onChange={handleChange}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Notas Internas</Label>
              <Textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Notas sobre a abordagem da proposta..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            variant="outline"
            type="button"
            onClick={() => navigate('/proposals')}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            <Save className="h-4 w-4 mr-2" />
            {isLoading ? 'A criar...' : 'Criar Proposta'}
          </Button>
        </div>
      </form>
    </div>
  );
}
