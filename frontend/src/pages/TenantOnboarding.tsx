import { useEffect, useMemo, useState } from 'react';
import { Building2, Check, ChevronLeft, ChevronRight, Loader2, Save } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  apiGetCurrentTenant,
  apiGetTenantIntelligenceProfile,
  apiGetTenantProfile,
  apiGetTenantStrategy,
  apiSubmitTenantOnboarding,
  type ApiTenant,
} from '@/lib/api';

const steps = [
  'Organizacao',
  'Capacidades',
  'Mercados',
  'Oportunidades',
  'Go/No-Go',
  'IA',
  'Revisao',
];

const emptyForm = {
  organization_type: 'consulting_firm',
  size: 'small',
  maturity_level: 'growing',
  primary_country: '',
  default_language: 'pt',
  legal_name: '',
  brand_name: '',
  website: '',
  organization_description: '',
  countries_of_operation: '',
  languages: 'pt, en',
  core_capabilities: '',
  certifications: '',
  past_clients: '',
  donor_experience: '',
  sector_experience: '',
  team_size: '0',
  annual_bid_capacity: '0',
  average_contract_size: '',
  preferred_contract_size: '',
  strategic_objectives: '',
  target_markets: '',
  target_donors: '',
  target_sectors: '',
  target_countries: '',
  priority_project_types: '',
  growth_goals: '',
  positioning_statement: '',
  risk_appetite: 'balanced',
  partnership_strategy: '',
  go_no_go_must_have: '',
  go_no_go_red_flags: '',
  go_no_go_minimum_team: '',
  go_no_go_notes: '',
  opportunity_keywords: '',
  excluded_keywords: '',
  preferred_sources: '',
  excluded_sources: '',
  preferred_procurement_types: '',
  minimum_score_threshold: '60',
  deadline_min_days: '',
  deadline_max_days: '',
  minimum_budget: '',
  maximum_budget: '',
  requires_local_partner: false,
  eligible_languages: 'pt, en',
  ai_instructions: '',
};

type FormState = typeof emptyForm;

function list(value: string) {
  return value.split(',').map((item) => item.trim()).filter(Boolean);
}

function numberOrNull(value: string) {
  return value.trim() ? Number(value) : null;
}

function moneyOrNull(value: string) {
  return value.trim() ? value.trim() : null;
}

export function TenantOnboarding() {
  const [tenant, setTenant] = useState<ApiTenant | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const current = await apiGetCurrentTenant();
        const [profile, strategy, intelligence] = await Promise.all([
          apiGetTenantProfile(current.id),
          apiGetTenantStrategy(current.id),
          apiGetTenantIntelligenceProfile(current.id),
        ]);
        if (!mounted) return;
        setTenant(current);
        setForm({
          organization_type: current.organization_type || 'consulting_firm',
          size: current.size || 'small',
          maturity_level: current.maturity_level || 'growing',
          primary_country: current.primary_country || '',
          default_language: current.default_language || 'pt',
          legal_name: profile.legal_name || '',
          brand_name: profile.brand_name || '',
          website: profile.website || '',
          organization_description: profile.organization_description || '',
          countries_of_operation: profile.countries_of_operation.join(', '),
          languages: profile.languages.join(', ') || 'pt, en',
          core_capabilities: profile.core_capabilities.join(', '),
          certifications: profile.certifications.join(', '),
          past_clients: profile.past_clients.join(', '),
          donor_experience: profile.donor_experience.join(', '),
          sector_experience: profile.sector_experience.join(', '),
          team_size: String(profile.team_size || 0),
          annual_bid_capacity: String(profile.annual_bid_capacity || 0),
          average_contract_size: profile.average_contract_size || '',
          preferred_contract_size: profile.preferred_contract_size || '',
          strategic_objectives: strategy.strategic_objectives.join(', '),
          target_markets: strategy.target_markets.join(', '),
          target_donors: strategy.target_donors.join(', '),
          target_sectors: strategy.target_sectors.join(', '),
          target_countries: strategy.target_countries.join(', '),
          priority_project_types: strategy.priority_project_types.join(', '),
          growth_goals: strategy.growth_goals.join(', '),
          positioning_statement: strategy.positioning_statement || '',
          risk_appetite: strategy.risk_appetite || 'balanced',
          partnership_strategy: strategy.partnership_strategy || '',
          go_no_go_must_have: Array.isArray(strategy.go_no_go_preferences?.must_have)
            ? strategy.go_no_go_preferences.must_have.join(', ')
            : '',
          go_no_go_red_flags: Array.isArray(strategy.go_no_go_preferences?.red_flags)
            ? strategy.go_no_go_preferences.red_flags.join(', ')
            : '',
          go_no_go_minimum_team: String(strategy.go_no_go_preferences?.minimum_team_size || ''),
          go_no_go_notes: String(strategy.go_no_go_preferences?.notes || ''),
          opportunity_keywords: intelligence.opportunity_keywords.join(', '),
          excluded_keywords: intelligence.excluded_keywords.join(', '),
          preferred_sources: intelligence.preferred_sources.join(', '),
          excluded_sources: intelligence.excluded_sources.join(', '),
          preferred_procurement_types: intelligence.preferred_procurement_types.join(', '),
          minimum_score_threshold: String(intelligence.minimum_score_threshold || 60),
          deadline_min_days: intelligence.deadline_min_days ? String(intelligence.deadline_min_days) : '',
          deadline_max_days: intelligence.deadline_max_days ? String(intelligence.deadline_max_days) : '',
          minimum_budget: intelligence.minimum_budget || '',
          maximum_budget: intelligence.maximum_budget || '',
          requires_local_partner: intelligence.requires_local_partner,
          eligible_languages: intelligence.eligible_languages.join(', ') || 'pt, en',
          ai_instructions: intelligence.ai_instructions || '',
        });
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Erro ao carregar tenant');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  const completion = useMemo(() => Math.round(((step + 1) / steps.length) * 100), [step]);

  const update = (key: keyof FormState, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const responses = () => ({
    organization: {
      organization_type: form.organization_type,
      size: form.size,
      maturity_level: form.maturity_level,
      primary_country: form.primary_country,
      default_language: form.default_language,
      legal_name: form.legal_name,
      brand_name: form.brand_name,
      website: form.website,
      organization_description: form.organization_description,
      countries_of_operation: list(form.countries_of_operation),
      languages: list(form.languages),
    },
    capabilities: {
      core_capabilities: list(form.core_capabilities),
      certifications: list(form.certifications),
      past_clients: list(form.past_clients),
      donor_experience: list(form.donor_experience),
      sector_experience: list(form.sector_experience),
      team_size: Number(form.team_size || 0),
      annual_bid_capacity: Number(form.annual_bid_capacity || 0),
      average_contract_size: moneyOrNull(form.average_contract_size),
      preferred_contract_size: moneyOrNull(form.preferred_contract_size),
    },
    markets: {
      strategic_objectives: list(form.strategic_objectives),
      target_markets: list(form.target_markets),
      target_donors: list(form.target_donors),
      target_sectors: list(form.target_sectors),
      target_countries: list(form.target_countries),
      priority_project_types: list(form.priority_project_types),
      growth_goals: list(form.growth_goals),
      positioning_statement: form.positioning_statement,
      risk_appetite: form.risk_appetite,
      partnership_strategy: form.partnership_strategy,
    },
    opportunity_preferences: {
      opportunity_keywords: list(form.opportunity_keywords),
      excluded_keywords: list(form.excluded_keywords),
      preferred_sources: list(form.preferred_sources),
      excluded_sources: list(form.excluded_sources),
      preferred_procurement_types: list(form.preferred_procurement_types),
      minimum_score_threshold: Number(form.minimum_score_threshold || 60),
      deadline_min_days: numberOrNull(form.deadline_min_days),
      deadline_max_days: numberOrNull(form.deadline_max_days),
      minimum_budget: moneyOrNull(form.minimum_budget),
      maximum_budget: moneyOrNull(form.maximum_budget),
      requires_local_partner: form.requires_local_partner,
      eligible_languages: list(form.eligible_languages),
    },
    go_no_go_preferences: {
      go_no_go_preferences: {
        must_have: list(form.go_no_go_must_have),
        red_flags: list(form.go_no_go_red_flags),
        minimum_team_size: numberOrNull(form.go_no_go_minimum_team),
        notes: form.go_no_go_notes,
      },
    },
    ai_positioning: {
      ai_instructions: form.ai_instructions,
    },
  });

  const preview = responses();

  const save = async () => {
    if (!tenant) return;
    setSaving(true);
    try {
      await apiSubmitTenantOnboarding(tenant.id, responses());
      toast.success('Onboarding guardado e perfil de inteligencia atualizado');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erro ao guardar onboarding');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4" />
            <span>{tenant?.name}</span>
          </div>
          <h1 className="text-2xl font-semibold tracking-normal">Onboarding do tenant</h1>
        </div>
        <Button onClick={save} disabled={saving}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Guardar
        </Button>
      </div>

      <div className="h-2 w-full overflow-hidden rounded bg-muted">
        <div className="h-full bg-primary transition-all" style={{ width: `${completion}%` }} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
        <nav className="space-y-1">
          {steps.map((label, index) => (
            <button
              key={label}
              className={`flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm ${
                index === step ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted'
              }`}
              onClick={() => setStep(index)}
            >
              {index < step ? <Check className="h-4 w-4" /> : <span className="h-4 w-4 rounded-full border" />}
              {label}
            </button>
          ))}
        </nav>

        <Card>
          <CardHeader>
            <CardTitle>{steps[step]}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            {step === 0 && (
              <>
                <Field label="Nome legal" value={form.legal_name} onChange={(v) => update('legal_name', v)} />
                <Field label="Marca" value={form.brand_name} onChange={(v) => update('brand_name', v)} />
                <Field label="Website" value={form.website} onChange={(v) => update('website', v)} />
                <Field label="Pais principal" value={form.primary_country} onChange={(v) => update('primary_country', v)} />
                <div className="space-y-2">
                  <Label>Tipo de organizacao</Label>
                  <Select value={form.organization_type} onValueChange={(v) => update('organization_type', v)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="consulting_firm">Consultoria</SelectItem>
                      <SelectItem value="ngo">ONG</SelectItem>
                      <SelectItem value="donor">Doador</SelectItem>
                      <SelectItem value="government">Governo</SelectItem>
                      <SelectItem value="startup">Startup</SelectItem>
                      <SelectItem value="university">Universidade</SelectItem>
                      <SelectItem value="other">Outro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Maturidade</Label>
                  <Select value={form.maturity_level} onValueChange={(v) => update('maturity_level', v)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="early">Inicial</SelectItem>
                      <SelectItem value="growing">Em crescimento</SelectItem>
                      <SelectItem value="mature">Madura</SelectItem>
                      <SelectItem value="advanced">Avancada</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Field label="Paises de operacao" value={form.countries_of_operation} onChange={(v) => update('countries_of_operation', v)} />
                <LongField label="Descricao da organizacao" value={form.organization_description} onChange={(v) => update('organization_description', v)} />
              </>
            )}
            {step === 1 && (
              <>
                <Field label="Idiomas" value={form.languages} onChange={(v) => update('languages', v)} />
                <Field label="Capacidades core" value={form.core_capabilities} onChange={(v) => update('core_capabilities', v)} />
                <Field label="Certificacoes" value={form.certifications} onChange={(v) => update('certifications', v)} />
                <Field label="Clientes anteriores" value={form.past_clients} onChange={(v) => update('past_clients', v)} />
                <Field label="Experiencia com doadores" value={form.donor_experience} onChange={(v) => update('donor_experience', v)} />
                <Field label="Experiencia sectorial" value={form.sector_experience} onChange={(v) => update('sector_experience', v)} />
                <Field label="Tamanho da equipa" type="number" value={form.team_size} onChange={(v) => update('team_size', v)} />
                <Field label="Capacidade anual de bids" type="number" value={form.annual_bid_capacity} onChange={(v) => update('annual_bid_capacity', v)} />
              </>
            )}
            {step === 2 && (
              <>
                <Field label="Objetivos estrategicos" value={form.strategic_objectives} onChange={(v) => update('strategic_objectives', v)} />
                <Field label="Mercados alvo" value={form.target_markets} onChange={(v) => update('target_markets', v)} />
                <Field label="Doadores alvo" value={form.target_donors} onChange={(v) => update('target_donors', v)} />
                <Field label="Setores alvo" value={form.target_sectors} onChange={(v) => update('target_sectors', v)} />
                <Field label="Paises alvo" value={form.target_countries} onChange={(v) => update('target_countries', v)} />
                <Field label="Tipos de projeto" value={form.priority_project_types} onChange={(v) => update('priority_project_types', v)} />
                <Field label="Objetivos de crescimento" value={form.growth_goals} onChange={(v) => update('growth_goals', v)} />
                <LongField label="Posicionamento" value={form.positioning_statement} onChange={(v) => update('positioning_statement', v)} />
              </>
            )}
            {step === 3 && (
              <>
                <Field label="Keywords de oportunidade" value={form.opportunity_keywords} onChange={(v) => update('opportunity_keywords', v)} />
                <Field label="Keywords a excluir" value={form.excluded_keywords} onChange={(v) => update('excluded_keywords', v)} />
                <Field label="Fontes preferidas" value={form.preferred_sources} onChange={(v) => update('preferred_sources', v)} />
                <Field label="Fontes excluidas" value={form.excluded_sources} onChange={(v) => update('excluded_sources', v)} />
                <Field label="Tipos de procurement" value={form.preferred_procurement_types} onChange={(v) => update('preferred_procurement_types', v)} />
                <Field label="Score minimo" type="number" value={form.minimum_score_threshold} onChange={(v) => update('minimum_score_threshold', v)} />
                <Field label="Budget minimo" value={form.minimum_budget} onChange={(v) => update('minimum_budget', v)} />
                <Field label="Budget maximo" value={form.maximum_budget} onChange={(v) => update('maximum_budget', v)} />
                <Field label="Deadline minimo (dias)" type="number" value={form.deadline_min_days} onChange={(v) => update('deadline_min_days', v)} />
                <Field label="Deadline maximo (dias)" type="number" value={form.deadline_max_days} onChange={(v) => update('deadline_max_days', v)} />
              </>
            )}
            {step === 4 && (
              <>
                <Field label="Must-have para go" value={form.go_no_go_must_have} onChange={(v) => update('go_no_go_must_have', v)} />
                <Field label="Red flags/no-go" value={form.go_no_go_red_flags} onChange={(v) => update('go_no_go_red_flags', v)} />
                <Field label="Equipa minima" type="number" value={form.go_no_go_minimum_team} onChange={(v) => update('go_no_go_minimum_team', v)} />
                <div className="space-y-2">
                  <Label>Apetite de risco</Label>
                  <Select value={form.risk_appetite} onValueChange={(v) => update('risk_appetite', v)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conservative">Conservador</SelectItem>
                      <SelectItem value="balanced">Equilibrado</SelectItem>
                      <SelectItem value="aggressive">Agressivo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center justify-between rounded border p-3 md:col-span-2">
                  <Label>Requer parceiro local por defeito</Label>
                  <Switch checked={form.requires_local_partner} onCheckedChange={(v) => update('requires_local_partner', v)} />
                </div>
                <LongField label="Estrategia de parcerias" value={form.partnership_strategy} onChange={(v) => update('partnership_strategy', v)} />
                <LongField label="Notas Go/No-Go" value={form.go_no_go_notes} onChange={(v) => update('go_no_go_notes', v)} />
              </>
            )}
            {step === 5 && (
              <>
                <Field label="Idiomas elegiveis" value={form.eligible_languages} onChange={(v) => update('eligible_languages', v)} />
                <LongField label="Instrucoes para IA" value={form.ai_instructions} onChange={(v) => update('ai_instructions', v)} />
              </>
            )}
            {step === 6 && (
              <div className="space-y-4 md:col-span-2">
                <ReviewBlock title="Organizacao" items={[
                  form.brand_name || form.legal_name || tenant?.name || '',
                  form.primary_country,
                  form.maturity_level,
                ]} />
                <ReviewBlock title="Mercados e capacidades" items={[
                  form.core_capabilities,
                  form.target_sectors,
                  form.target_countries,
                  form.target_donors,
                ]} />
                <ReviewBlock title="Inteligencia" items={[
                  form.opportunity_keywords,
                  form.excluded_keywords,
                  `Score minimo: ${form.minimum_score_threshold}`,
                  form.requires_local_partner ? 'Requer parceiro local' : '',
                ]} />
                <pre className="max-h-72 overflow-auto rounded border bg-muted p-3 text-xs">
                  {JSON.stringify(preview, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Anterior
        </Button>
        <Button onClick={() => setStep((s) => Math.min(steps.length - 1, s + 1))} disabled={step === steps.length - 1}>
          Seguinte
          <ChevronRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function ReviewBlock({ title, items }: { title: string; items: string[] }) {
  const visibleItems = items.filter(Boolean);
  return (
    <section className="space-y-2">
      <h3 className="text-sm font-medium">{title}</h3>
      <div className="grid gap-2 md:grid-cols-2">
        {visibleItems.map((item) => (
          <div key={item} className="rounded border px-3 py-2 text-sm">{item}</div>
        ))}
      </div>
    </section>
  );
}

function Field({ label, value, onChange, type = 'text' }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function LongField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2 md:col-span-2">
      <Label>{label}</Label>
      <Textarea value={value} onChange={(event) => onChange(event.target.value)} rows={5} />
    </div>
  );
}
