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
import { Textarea } from '@/components/ui/textarea';
import { Plus } from 'lucide-react';
import { useOpportunityStore } from '@/stores';

export function AddOpportunityModal() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    title: '',
    client: '',
    sector: '',
    country: '',
    value: '',
    currency: 'USD',
    deadline: '',
    description: '',
  });
  const { addOpportunity } = useOpportunityStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    addOpportunity({
      ...form,
      value: Number(form.value),
      deadline: new Date(form.deadline),
    } as any);
    setOpen(false);
    setForm({
      title: '', client: '', sector: '', country: '',
      value: '', currency: 'USD', deadline: '', description: '',
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Nova Oportunidade
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Nova Oportunidade</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Título</Label>
            <Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Cliente</Label>
              <Input value={form.client} onChange={e => setForm({ ...form, client: e.target.value })} required />
            </div>
            <div>
              <Label>Setor</Label>
              <Input value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })} required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>País</Label>
              <Input value={form.country} onChange={e => setForm({ ...form, country: e.target.value })} required />
            </div>
            <div>
              <Label>Valor (USD)</Label>
              <Input type="number" value={form.value} onChange={e => setForm({ ...form, value: e.target.value })} required />
            </div>
          </div>
          <div>
            <Label>Prazo</Label>
            <Input type="datetime-local" value={form.deadline} onChange={e => setForm({ ...form, deadline: e.target.value })} required />
          </div>
          <div>
            <Label>Descrição</Label>
            <Textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} />
          </div>
          <Button type="submit" className="w-full">
            {'Criar Oportunidade'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
