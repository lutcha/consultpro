// ============================================
// NEW OPPORTUNITY PAGE
// ============================================

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Upload } from 'lucide-react';
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
import { apiCreateOpportunity, apiUploadToR } from '@/lib/api';

const SECTORS = [
  'Educação',
  'Saúde',
  'Agricultura',
  'Infraestruturas',
  'Governação',
  'Ambiental',
  'Tecnologia',
  'Finanças',
];

const COUNTRIES = [
  'Moçambique',
  'Angola',
  'Cabo Verde',
  'Senegal',
  'Guiné-Bissau',
  'Timor-Leste',
  'São Tomé e Príncipe',
  'Outro',
];

const CURRENCIES = ['USD', 'EUR', 'GBP'];

export function NewOpportunity() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [torFile, setTorFile] = useState<File | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    client: '',
    sector: '',
    country: '',
    value: '',
    currency: 'USD',
    deadline: '',
    description: '',
    evaluation_criteria: '',
    technical_weight: 70,
    financial_weight: 30,
    reference_number: '',
    url_source: '',
  });

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
      const opportunity = await apiCreateOpportunity({
        ...formData,
        value: formData.value,
        status: 'new',
      });

      // Upload ToR if selected
      if (torFile && opportunity.id) {
        await apiUploadToR(String(opportunity.id), torFile);
      }

      navigate(`/opportunities/${opportunity.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar oportunidade');
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/opportunities')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
        <h1 className="text-2xl font-bold">Nova Oportunidade</h1>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Informações da Oportunidade</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Título *</Label>
              <Input
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="Ex: Avaliação de Impacto - Programa de Educação"
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
                  placeholder="Ex: UNICEF, Banco Mundial"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reference_number">Nº de Referência</Label>
                <Input
                  id="reference_number"
                  name="reference_number"
                  value={formData.reference_number}
                  onChange={handleChange}
                  placeholder="Ex: TOR-2024-001"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sector">Setor *</Label>
                <Select
                  value={formData.sector}
                  onValueChange={(v) =>
                    setFormData((prev) => ({ ...prev, sector: v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecionar setor" />
                  </SelectTrigger>
                  <SelectContent>
                    {SECTORS.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="country">País *</Label>
                <Select
                  value={formData.country}
                  onValueChange={(v) =>
                    setFormData((prev) => ({ ...prev, country: v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecionar país" />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRIES.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="value">Valor *</Label>
                <Input
                  id="value"
                  name="value"
                  type="number"
                  value={formData.value}
                  onChange={handleChange}
                  placeholder="450000"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="currency">Moeda</Label>
                <Select
                  value={formData.currency}
                  onValueChange={(v) =>
                    setFormData((prev) => ({ ...prev, currency: v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="deadline">Prazo *</Label>
                <Input
                  id="deadline"
                  name="deadline"
                  type="date"
                  value={formData.deadline}
                  onChange={handleChange}
                  required
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
                placeholder="Descreva a oportunidade..."
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="evaluation_criteria">Critérios de Avaliação</Label>
              <Textarea
                id="evaluation_criteria"
                name="evaluation_criteria"
                value={formData.evaluation_criteria}
                onChange={handleChange}
                placeholder="QCBS, LCS, etc."
                rows={2}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="technical_weight">Peso Técnico (%)</Label>
                <Input
                  id="technical_weight"
                  name="technical_weight"
                  type="number"
                  min={0}
                  max={100}
                  value={formData.technical_weight}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="financial_weight">Peso Financeiro (%)</Label>
                <Input
                  id="financial_weight"
                  name="financial_weight"
                  type="number"
                  min={0}
                  max={100}
                  value={formData.financial_weight}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="url_source">URL da Fonte</Label>
              <Input
                id="url_source"
                name="url_source"
                type="url"
                value={formData.url_source}
                onChange={handleChange}
                placeholder="https://..."
              />
            </div>

            {/* ToR Upload */}
            <div className="space-y-2">
              <Label>Documento ToR</Label>
              <div className="flex items-center gap-4">
                <Input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => setTorFile(e.target.files?.[0] || null)}
                  className="flex-1"
                />
                {torFile && (
                  <span className="text-sm text-muted-foreground">
                    <Upload className="h-4 w-4 inline mr-1" />
                    {torFile.name}
                  </span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4 mt-6">
          <Button
            variant="outline"
            type="button"
            onClick={() => navigate('/opportunities')}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            <Save className="h-4 w-4 mr-2" />
            {isLoading ? 'A criar...' : 'Criar Oportunidade'}
          </Button>
        </div>
      </form>
    </div>
  );
}
