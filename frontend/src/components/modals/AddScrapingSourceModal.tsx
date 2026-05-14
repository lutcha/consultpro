import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus } from 'lucide-react';
import { apiCreateScrapingSource } from '@/lib/api';
import { toast } from 'sonner';

interface Props {
  open?: boolean;
  onClose?: () => void;
  onAdd?: (data: any) => void;
}

export function AddScrapingSourceModal({ open, onClose, onAdd }: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    organization: '',
    url: '',
    source_type: 'portal',
    scrape_frequency: 'daily',
  });
  const [isSaving, setIsSaving] = useState(false);

  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : internalOpen;

  const handleOpenChange = (v: boolean) => {
    if (!isControlled) setInternalOpen(v);
    if (!v && onClose) onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      name: form.name,
      organization: form.organization,
      url: form.url,
      source_type: form.source_type,
      scrape_frequency: form.scrape_frequency,
    };
    setIsSaving(true);
    try {
      if (onAdd) {
        await Promise.resolve(onAdd(data));
      } else {
        await apiCreateScrapingSource(data);
        toast.success('Fonte criada');
      }
      handleOpenChange(false);
      setForm({ name: '', organization: '', url: '', source_type: 'portal', scrape_frequency: 'daily' });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro ao criar fonte');
    } finally {
      setIsSaving(false);
    }
  };

  const dialogContent = (
    <DialogContent className="max-w-lg">
      <DialogHeader>
        <DialogTitle>Nova Fonte de Scraping</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Nome</Label>
          <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div>
          <Label>Organização</Label>
          <Input value={form.organization} onChange={e => setForm({ ...form, organization: e.target.value })} required />
        </div>
        <div>
          <Label>URL</Label>
          <Input type="url" value={form.url} onChange={e => setForm({ ...form, url: e.target.value })} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Tipo</Label>
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3"
              value={form.source_type}
              onChange={e => setForm({ ...form, source_type: e.target.value })}
            >
              <option value="portal">Portal</option>
              <option value="rss">RSS Feed</option>
              <option value="api">API</option>
              <option value="job_board">Job Board</option>
            </select>
          </div>
          <div>
            <Label>Frequência</Label>
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3"
              value={form.scrape_frequency}
              onChange={e => setForm({ ...form, scrape_frequency: e.target.value })}
            >
              <option value="hourly">Por Hora</option>
              <option value="daily">Diário</option>
              <option value="weekly">Semanal</option>
            </select>
          </div>
        </div>
        <Button type="submit" className="w-full" disabled={isSaving}>
          {isSaving ? 'A adicionar...' : 'Adicionar Fonte'}
        </Button>
      </form>
    </DialogContent>
  );

  if (isControlled) {
    return (
      <Dialog open={isOpen} onOpenChange={handleOpenChange}>
        {dialogContent}
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Nova Fonte
        </Button>
      </DialogTrigger>
      {dialogContent}
    </Dialog>
  );
}
