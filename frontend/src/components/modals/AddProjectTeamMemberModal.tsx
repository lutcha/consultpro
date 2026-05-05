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
  projectName?: string;
}

export function AddProjectTeamMemberModal({ open, onClose, onAdd, projectName }: Props) {
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [type, setType] = useState<'internal' | 'external'>('internal');

  const handleSubmit = () => {
    if (!name.trim() || !role.trim()) return;
    onAdd({ id: `new-${Date.now()}`, name: name.trim(), role: role.trim(), type });
    setName(''); setRole(''); setType('internal');
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Adicionar Membro ao Projeto
            {projectName && <span className="text-sm font-normal text-muted-foreground">— {projectName}</span>}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <Label>Tipo</Label>
            <div className="flex gap-2 mt-1.5">
              <button onClick={() => setType('internal')} className={`flex-1 text-sm px-3 py-2 rounded-md border transition-colors ${type==='internal'?'bg-primary text-primary-foreground border-primary':'bg-background hover:bg-muted'}`}>Membro Interno</button>
              <button onClick={() => setType('external')} className={`flex-1 text-sm px-3 py-2 rounded-md border transition-colors ${type==='external'?'bg-emerald-600 text-white border-emerald-600':'bg-background hover:bg-muted'}`}>Consultor Externo</button>
            </div>
          </div>
          <div><Label>Nome</Label><Input value={name} onChange={(e)=>setName(e.target.value)} placeholder="Nome completo" /></div>
          <div><Label>Funcao no Projeto</Label><Input value={role} onChange={(e)=>setRole(e.target.value)} placeholder="Ex: Especialista em Saude" /></div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || !role.trim()}>Adicionar Membro</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
