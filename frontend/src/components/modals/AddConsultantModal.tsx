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

export function AddConsultantModal({ open, onClose, onAdd }: Props) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [seniority, setSeniority] = useState('mid');
  const [sector, setSector] = useState('Saude');
  const [location, setLocation] = useState('');
  const [dailyRate, setDailyRate] = useState('');
  const [skills, setSkills] = useState('');

  const handleSubmit = () => {
    if (!name.trim() || !email.trim()) return;
    onAdd({
      name: name.trim(),
      email: email.trim(),
      seniority,
      seniorityLabel: seniority === 'senior' ? 'Senior' : seniority === 'mid' ? 'Mid-Level' : 'Junior',
      sector,
      sectors: [sector],
      location: location.trim() || 'Nao especificado',
      availability: 'available',
      education: 'Nao especificado',
      yearsExperience: 0,
      projectsCompleted: 0,
      dailyRate: Number(dailyRate) || 0,
      currency: 'EUR',
      rating: 0,
      skills: skills.split(',').map((s) => s.trim()).filter(Boolean),
      languages: ['Portugues'],
      lastProject: { name: 'Nenhum', date: '-' },
    });
    setName(''); setEmail(''); setSeniority('mid'); setSector('Saude'); setLocation(''); setDailyRate(''); setSkills('');
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Novo Consultor Externo
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div><Label>Nome Completo</Label><Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex: Carlos Mendes" /></div>
          <div><Label>Email</Label><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="carlos.mendes@email.com" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Senioridade</Label>
              <select className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm" value={seniority} onChange={(e) => setSeniority(e.target.value)}>
                <option value="senior">Senior</option>
                <option value="mid">Mid-Level</option>
                <option value="junior">Junior</option>
              </select>
            </div>
            <div><Label>Setor Principal</Label>
              <select className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm" value={sector} onChange={(e) => setSector(e.target.value)}>
                <option value="Saude">Saude</option>
                <option value="Educacao">Educacao</option>
                <option value="Governanca">Governanca</option>
                <option value="Agricultura">Agricultura</option>
                <option value="Ambiente">Ambiente</option>
                <option value="Infraestruturas">Infraestruturas</option>
                <option value="Economia">Economia</option>
                <option value="Tecnologia">Tecnologia</option>
              </select>
            </div>
          </div>
          <div><Label>Localizacao</Label><Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Ex: Lisboa, Portugal" /></div>
          <div><Label>Taxa Diaria (EUR)</Label><Input type="number" value={dailyRate} onChange={(e) => setDailyRate(e.target.value)} placeholder="Ex: 450" /></div>
          <div><Label>Skills (separadas por virgula)</Label><Input value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="Ex: Gestao de Projetos, M&E, Saude Publica" /></div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || !email.trim()}>Adicionar Consultor</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
