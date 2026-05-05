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
import { useProposalStore, useOpportunityStore } from '@/stores';

export function AddProposalModal() {
  const [open, setOpen] = useState(false);
  const [opportunityId, setOpportunityId] = useState('');
  const [title, setTitle] = useState('');
  const { addProposal } = useProposalStore();
  const { opportunities } = useOpportunityStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    addProposal({ opportunityId, title } as any);
    setOpen(false);
    setOpportunityId('');
    setTitle('');
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Nova Proposta
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Nova Proposta</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Oportunidade</Label>
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3"
              value={opportunityId}
              onChange={e => setOpportunityId(e.target.value)}
              required
            >
              <option value="">Selecionar oportunidade</option>
              {opportunities.map((o) => (
                <option key={o.id} value={o.id}>{o.title}</option>
              ))}
            </select>
          </div>
          <div>
            <Label>Título da Proposta</Label>
            <Input value={title} onChange={e => setTitle(e.target.value)} required />
          </div>
          <Button type="submit" className="w-full">
            {'Criar Proposta'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
