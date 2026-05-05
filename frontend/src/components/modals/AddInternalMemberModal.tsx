import { useState } from 'react';
import { UserPlus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Props {
  open: boolean;
  onClose: () => void;
  onAdd: (data: any) => void;
}

export function AddInternalMemberModal({ open, onClose, onAdd }: Props) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('');
  const [phase, setPhase] = useState('Prospeccao');
  const [skills, setSkills] = useState('');

  const handleSubmit = () => {
    if (!name.trim() || !email.trim() || !role.trim()) return;
    onAdd({
      name: name.trim(),
      email: email.trim(),
      role: role.trim(),
      phase,
      availability: 'available',
      projectsCount: 0,
      skills: skills.split(',').map((s) => s.trim()).filter(Boolean),
    });
    setName(''); setEmail(''); setRole(''); setPhase('Prospeccao'); setSkills('');
    onClose();
  };

  const phases = ['Prospeccao', 'Analise', 'Proposta', 'Negociacao', 'Execucao', 'Fecho'];

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Novo Membro Interno
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div><Label>Nome Completo</Label><Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex: Maria Santos" /></div>
          <div><Label>Email</Label><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="maria.santos@consultpro.pt" /></div>
          <div><Label>Funcao</Label><Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Ex: Analista de Propostas" /></div>
          <div><Label>Fase Pipeline</Label>
            <select className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm" value={phase} onChange={(e) => setPhase(e.target.value)}>
              {phases.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div><Label>Skills (separadas por virgula)</Label><Input value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="Ex: Propostas, Analise, PMO" /></div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || !email.trim() || !role.trim()}>Adicionar Membro</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
