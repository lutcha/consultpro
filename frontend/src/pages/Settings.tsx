// ============================================
// SETTINGS PAGE - Complete Configuration
// ============================================

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  User,
  Lock,
  Bell,
  FileText,
  Globe,
  Users,
  Moon,
  Sun,
  Monitor,
  Plus,
  Pencil,
  Trash2,
  RefreshCw,
  Palette,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useUserStore } from '@/stores';
import { useCurriculumStore } from '@/stores/useCurriculumStore';
import { useScrapingStore } from '@/stores/useScrapingStore';
import { apiUpdateMe } from '@/lib/api';
import { toast } from 'sonner';
import type { CVTemplate } from '@/types';

const ORG_OPTIONS = [
  { value: 'world_bank', label: 'World Bank' },
  { value: 'un', label: 'United Nations' },
  { value: 'eu', label: 'European Union' },
  { value: 'afdb', label: 'African Development Bank' },
  { value: 'usaid', label: 'USAID' },
  { value: 'giz', label: 'GIZ' },
  { value: 'other', label: 'Other' },
];

interface TemplateFormState {
  name: string;
  organization: string;
  organization_name: string;
  description: string;
  max_length_pages: string;
}

const BLANK_FORM: TemplateFormState = {
  name: '', organization: 'world_bank', organization_name: 'World Bank',
  description: '', max_length_pages: '',
};

export function Settings() {
  const navigate = useNavigate();
  const { user, setUser } = useUserStore();
  const {
    templates, isLoadingTemplates,
    fetchTemplates, createTemplate, updateTemplate, deleteTemplate,
  } = useCurriculumStore();
  const { sources, fetchSources } = useScrapingStore();
  const [isLoading, setIsLoading] = useState(false);

  const [templateModal, setTemplateModal] = useState<{ open: boolean; editing: CVTemplate | null }>({ open: false, editing: null });
  const [templateForm, setTemplateForm] = useState<TemplateFormState>(BLANK_FORM);
  const [templateSaving, setTemplateSaving] = useState(false);
  const [templateDeleting, setTemplateDeleting] = useState<string | null>(null);

  const [profile, setProfile] = useState({
    first_name: user?.name?.split(' ')[0] || '',
    last_name: user?.name?.split(' ').slice(1).join(' ') || '',
    email: user?.email || '',
    phone: '',
    bio: '',
    location: '',
  });

  const [password, setPassword] = useState({
    current: '',
    new: '',
    confirm: '',
  });

  const [notifications, setNotifications] = useState({
    email_deadlines: true,
    email_proposals: true,
    push_opportunities: false,
    push_qc: true,
    weekly_digest: true,
  });

  const [theme, setTheme] = useState('system');
  const [apiKey, setApiKey] = useState('sk-••••••••••••••••••••••••••••••');

  useEffect(() => {
    fetchTemplates();
    fetchSources();
  }, [fetchTemplates, fetchSources]);

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setProfile((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSaveProfile = async () => {
    setIsLoading(true);
    try {
      await apiUpdateMe(profile);
      setUser({ ...user!, name: `${profile.first_name} ${profile.last_name}`.trim(), email: profile.email });
      toast.success('Perfil atualizado com sucesso');
    } catch {
      toast.error('Erro ao atualizar perfil');
    }
    setIsLoading(false);
  };

  const handlePasswordChange = async () => {
    if (password.new !== password.confirm) {
      toast.error('As palavras-passe não coincidem');
      return;
    }
    toast.info('Alteração de password - funcionalidade em desenvolvimento');
  };

  const handleNotificationToggle = (key: string) => {
    setNotifications((prev) => ({ ...prev, [key]: !prev[key as keyof typeof prev] }));
  };

  const handleRegenerateApiKey = () => {
    setApiKey(`sk-${Math.random().toString(36).substring(2, 18)}`);
    toast.success('API Key regenerada com sucesso');
  };

  const openNewTemplate = () => {
    setTemplateForm(BLANK_FORM);
    setTemplateModal({ open: true, editing: null });
  };

  const openEditTemplate = (t: CVTemplate) => {
    setTemplateForm({
      name: t.name,
      organization: t.organization,
      organization_name: t.organizationName,
      description: t.description || '',
      max_length_pages: t.maxLengthPages ? String(t.maxLengthPages) : '',
    });
    setTemplateModal({ open: true, editing: t });
  };

  const handleTemplateSave = async () => {
    if (!templateForm.name.trim()) { toast.error('Nome obrigatorio'); return; }
    setTemplateSaving(true);
    try {
      const payload = {
        name: templateForm.name.trim(),
        organization: templateForm.organization,
        organization_name: templateForm.organization_name || ORG_OPTIONS.find(o => o.value === templateForm.organization)?.label || templateForm.organization,
        description: templateForm.description.trim(),
        max_length_pages: templateForm.max_length_pages ? Number(templateForm.max_length_pages) : null,
        required_sections: [],
        format_rules: [],
        is_active: true,
      };
      if (templateModal.editing) {
        await updateTemplate(templateModal.editing.id, payload);
        toast.success('Template atualizado');
      } else {
        await createTemplate(payload);
        toast.success('Template criado');
      }
      setTemplateModal({ open: false, editing: null });
    } catch {
      toast.error('Erro ao guardar template');
    } finally {
      setTemplateSaving(false);
    }
  };

  const handleTemplateDelete = async (t: CVTemplate) => {
    setTemplateDeleting(t.id);
    try {
      await deleteTemplate(t.id);
      toast.success('Template removido');
    } catch {
      toast.error('Erro ao remover template');
    } finally {
      setTemplateDeleting(null);
    }
  };

  const handleOrgChange = (value: string) => {
    const label = ORG_OPTIONS.find(o => o.value === value)?.label || value;
    setTemplateForm(f => ({ ...f, organization: value, organization_name: label }));
  };

  const isAdmin = user?.role === 'admin';

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Definições</h1>
          <p className="text-muted-foreground">Configure a plataforma e a sua conta</p>
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 lg:grid-cols-7">
          <TabsTrigger value="profile"><User className="h-4 w-4 mr-1" /> Perfil</TabsTrigger>
          <TabsTrigger value="password"><Lock className="h-4 w-4 mr-1" /> Password</TabsTrigger>
          <TabsTrigger value="notifications"><Bell className="h-4 w-4 mr-1" /> Alertas</TabsTrigger>
          <TabsTrigger value="templates"><FileText className="h-4 w-4 mr-1" /> Templates</TabsTrigger>
          <TabsTrigger value="scraping"><Globe className="h-4 w-4 mr-1" /> Scraping</TabsTrigger>
          {isAdmin && <TabsTrigger value="users"><Users className="h-4 w-4 mr-1" /> Utilizadores</TabsTrigger>}
          <TabsTrigger value="appearance"><Palette className="h-4 w-4 mr-1" /> Tema</TabsTrigger>
        </TabsList>

        {/* Profile */}
        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Perfil do Utilizador</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><Label>Nome</Label><Input name="first_name" value={profile.first_name} onChange={handleProfileChange} /></div>
                <div><Label>Apelido</Label><Input name="last_name" value={profile.last_name} onChange={handleProfileChange} /></div>
              </div>
              <div><Label>Email</Label><Input name="email" type="email" value={profile.email} onChange={handleProfileChange} /></div>
              <div><Label>Telefone</Label><Input name="phone" value={profile.phone} onChange={handleProfileChange} /></div>
              <div><Label>Localização</Label><Input name="location" value={profile.location} onChange={handleProfileChange} /></div>
              <div><Label>Bio</Label><Textarea name="bio" value={profile.bio} onChange={handleProfileChange} rows={3} /></div>
              <Button onClick={handleSaveProfile} disabled={isLoading}><Save className="h-4 w-4 mr-2" />Guardar Perfil</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Password */}
        <TabsContent value="password" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Alterar Password</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>Password Actual</Label><Input type="password" value={password.current} onChange={(e) => setPassword({ ...password, current: e.target.value })} /></div>
              <div><Label>Nova Password</Label><Input type="password" value={password.new} onChange={(e) => setPassword({ ...password, new: e.target.value })} /></div>
              <div><Label>Confirmar Nova Password</Label><Input type="password" value={password.confirm} onChange={(e) => setPassword({ ...password, confirm: e.target.value })} /></div>
              <Button onClick={handlePasswordChange}><Lock className="h-4 w-4 mr-2" />Alterar Password</Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>API Key</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input value={apiKey} readOnly />
                <Button variant="outline" onClick={handleRegenerateApiKey}><RefreshCw className="h-4 w-4 mr-2" />Regenerar</Button>
              </div>
              <p className="text-sm text-muted-foreground">Use esta chave para integrações externas com a API ConsultPro.</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Configuração de Notificações</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {[
                { key: 'email_deadlines', label: 'Alertas de prazos por email', desc: 'Receba notificações quando os prazos das oportunidades se aproximarem' },
                { key: 'email_proposals', label: 'Updates de propostas', desc: 'Notificações sobre alterações de estado nas propostas' },
                { key: 'push_opportunities', label: 'Novas oportunidades (Push)', desc: 'Receba alertas push quando novas oportunidades forem capturadas' },
                { key: 'push_qc', label: 'Resultados de Quality Check', desc: 'Notificações quando um QC for concluído' },
                { key: 'weekly_digest', label: 'Resumo semanal', desc: 'Email semanal com estatísticas e oportunidades relevantes' },
              ].map((item) => (
                <div key={item.key} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <p className="font-medium">{item.label}</p>
                    <p className="text-sm text-muted-foreground">{item.desc}</p>
                  </div>
                  <Switch
                    checked={notifications[item.key as keyof typeof notifications]}
                    onCheckedChange={() => handleNotificationToggle(item.key)}
                  />
                </div>
              ))}
              <Button onClick={() => toast.success('Preferências de notificações guardadas')}><Save className="h-4 w-4 mr-2" />Guardar Preferências</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Templates de CV</CardTitle>
              <Button size="sm" onClick={openNewTemplate}><Plus className="h-4 w-4 mr-1" />Novo Template</Button>
            </CardHeader>
            <CardContent>
              {isLoadingTemplates ? (
                <div className="flex items-center gap-2 py-4 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">A carregar templates...</span>
                </div>
              ) : templates.length === 0 ? (
                <p className="text-sm text-muted-foreground py-4 text-center">
                  Nenhum template configurado. Clique em <strong>Novo Template</strong> para adicionar.
                </p>
              ) : (
                <div className="space-y-3">
                  {templates.map((t) => (
                    <div key={t.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{t.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {t.organizationName}
                          {t.maxLengthPages && <> • {t.maxLengthPages} pag.</>}
                          {' '}• {t.requiredSections?.length || 0} secções
                        </p>
                      </div>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={() => openEditTemplate(t)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost" size="icon"
                          disabled={templateDeleting === t.id}
                          onClick={() => handleTemplateDelete(t)}
                        >
                          {templateDeleting === t.id
                            ? <Loader2 className="h-4 w-4 animate-spin" />
                            : <Trash2 className="h-4 w-4 text-destructive" />}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scraping */}
        <TabsContent value="scraping" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Fontes de Scraping</CardTitle>
              <Button size="sm"><Plus className="h-4 w-4 mr-1" />Nova Fonte</Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {sources.length === 0 && <p className="text-muted-foreground">Carregando fontes...</p>}
                {sources.map((s) => (
                  <div key={s.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{s.name}</p>
                      <p className="text-sm text-muted-foreground">{s.organization} • {s.scrapeFrequency}</p>
                    </div>
                    <Badge variant={s.status === 'active' ? 'default' : 'secondary'}>{s.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users (Admin only) */}
        {isAdmin && (
          <TabsContent value="users" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Gestão de Utilizadores</CardTitle>
                <Button size="sm"><Plus className="h-4 w-4 mr-1" />Convidar</Button>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Funcionalidade de gestão de utilizadores será implementada na próxima versão.</p>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Appearance */}
        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Tema</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${theme === 'light' ? 'border-primary bg-primary/5' : ''}`}
                  onClick={() => setTheme('light')}
                >
                  <Sun className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-center font-medium">Claro</p>
                </div>
                <div
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${theme === 'dark' ? 'border-primary bg-primary/5' : ''}`}
                  onClick={() => setTheme('dark')}
                >
                  <Moon className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-center font-medium">Escuro</p>
                </div>
                <div
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${theme === 'system' ? 'border-primary bg-primary/5' : ''}`}
                  onClick={() => setTheme('system')}
                >
                  <Monitor className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-center font-medium">Sistema</p>
                </div>
              </div>
              <Button onClick={() => toast.success('Tema aplicado')}><Save className="h-4 w-4 mr-2" />Aplicar Tema</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* CV Template Modal */}
      <Dialog open={templateModal.open} onOpenChange={(v) => { if (!v) setTemplateModal({ open: false, editing: null }); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{templateModal.editing ? 'Editar Template' : 'Novo Template de CV'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Nome do Template *</Label>
              <Input
                value={templateForm.name}
                onChange={(e) => setTemplateForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Ex: World Bank Standard CV"
              />
            </div>
            <div>
              <Label>Organizacao</Label>
              <Select value={templateForm.organization} onValueChange={handleOrgChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ORG_OPTIONS.map(o => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Nome da Organizacao (exibicao)</Label>
              <Input
                value={templateForm.organization_name}
                onChange={(e) => setTemplateForm(f => ({ ...f, organization_name: e.target.value }))}
                placeholder="Ex: World Bank / Banco Mundial"
              />
            </div>
            <div>
              <Label>Descricao</Label>
              <Textarea
                value={templateForm.description}
                onChange={(e) => setTemplateForm(f => ({ ...f, description: e.target.value }))}
                rows={3}
                placeholder="Descreva o formato e requisitos do template..."
              />
            </div>
            <div>
              <Label>Paginas Maximas</Label>
              <Input
                type="number"
                min={1}
                max={20}
                value={templateForm.max_length_pages}
                onChange={(e) => setTemplateForm(f => ({ ...f, max_length_pages: e.target.value }))}
                placeholder="Ex: 4"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTemplateModal({ open: false, editing: null })}>Cancelar</Button>
            <Button onClick={handleTemplateSave} disabled={templateSaving}>
              {templateSaving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />A guardar...</> : <><Save className="h-4 w-4 mr-2" />Guardar</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
