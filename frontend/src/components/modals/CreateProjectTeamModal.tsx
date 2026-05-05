import { useState } from 'react';
import { Briefcase } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Props {
  open: boolean;
  onClose: () => void;
  onAdd: (data: any) => void;
}

const PHASES = [
  'Prospeccao', 'Analise', 'Montagem Proposta', 'Metodologia',
  'Orcamento', 'Redacao/Revisao', 'Quality Assurance', 'Negociacao',
];

export function CreateProjectTeamModal({ open, onClose, onAdd }: Props) {
  const [name, setName] = useState('');
  const [client, setClient] = useState('');
  const [phase, setPhase] = useState('Montagem Proposta');

  const handleSubmit = () => {
    if (!name.trim() || !client.trim()) return;
    onAdd({
      id: `proj-${Date.now()}`,
      name: name.trim(),
      client: client.trim(),
      phase,
      status: 'in_proposal',
      internalMembers: [],
      externalMembers: [],
    });
    setName('');
    setClient('');
    setPhase('Montagem Proposta');
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" />
            Nova Equipa de Projeto
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <Label>Nome do Projeto / Proposta</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Proposta UNDP Moçambique 2025"
            />
          </div>
          <div>
            <Label>Cliente / Doador</Label>
            <Input
              value={client}
              onChange={(e) => setClient(e.target.value)}
              placeholder="Ex: UNDP, FAO, Banco Mundial"
            />
          </div>
          <div>
            <Label>Fase Atual</Label>
            <select
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
              value={phase}
              onChange={(e) => setPhase(e.target.value)}
            >
              {PHASES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button
            onClick={handleSubmit}
            disabled={!name.trim() || !client.trim()}
          >
            Criar Equipa
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
