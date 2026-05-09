import { useState } from 'react';
import { UserPlus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiCreateUser } from '@/lib/api';

interface Props {
  open: boolean;
  onClose: () => void;
  onAdd: () => void;
}

export function AddConsultantModal({ open, onClose, onAdd }: Props) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [skills, setSkills] = useState('');
  const [languages, setLanguages] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setFirstName(''); setLastName(''); setEmail(''); setSkills(''); setLanguages(''); setPassword(''); setError(null);
  };

  const handleSubmit = async () => {
    if (!firstName.trim() || !email.trim() || !password.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      await apiCreateUser({
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        password: password.trim(),
        role: 'consultant',
        skills: skills.split(',').map((s) => s.trim()).filter(Boolean),
        languages: languages.split(',').map((l) => l.trim()).filter(Boolean),
      });
      reset();
      onAdd();
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose(); } }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Novo Consultor Externo
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Primeiro Nome</Label><Input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Carlos" /></div>
            <div><Label>Apelido</Label><Input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Mendes" /></div>
          </div>
          <div><Label>Email</Label><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="carlos.mendes@email.com" /></div>
          <div><Label>Palavra-passe Temporaria</Label><Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 caracteres" /></div>
          <div><Label>Skills (separadas por virgula)</Label><Input value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="Ex: Gestao de Projetos, M&E, Saude Publica" /></div>
          <div><Label>Linguas (separadas por virgula)</Label><Input value={languages} onChange={(e) => setLanguages(e.target.value)} placeholder="Ex: PT, EN, FR" /></div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!firstName.trim() || !email.trim() || !password.trim() || isLoading}>
            {isLoading ? 'A criar...' : 'Adicionar Consultor'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
