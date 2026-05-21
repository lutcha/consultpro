import { useEffect, useState } from 'react';
import { AlertCircle, BookOpen, Loader2, Edit2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  apiGetProposalPostMortem,
  apiCreateProposalPostMortem,
  type ApiProposalPostMortem,
} from '@/lib/api';
import { cn } from '@/lib/utils';

const OUTCOME_CONFIG: Record<
  ApiProposalPostMortem['outcome'],
  { label: string; color: string }
> = {
  won: { label: 'Ganha', color: 'bg-emerald-100 text-emerald-700' },
  lost: { label: 'Perdida', color: 'bg-red-100 text-red-700' },
  cancelled: { label: 'Cancelada', color: 'bg-gray-100 text-gray-600' },
  no_decision: { label: 'Sem decisão', color: 'bg-amber-100 text-amber-700' },
};

interface FormState {
  outcome: ApiProposalPostMortem['outcome'];
  outcome_reason: string;
  client_feedback: string;
  lessons_learned_text: string;
}

const EMPTY_FORM: FormState = {
  outcome: 'no_decision',
  outcome_reason: '',
  client_feedback: '',
  lessons_learned_text: '',
};

interface Props {
  proposalId: string;
}

export function PostMortemPanel({ proposalId }: Props) {
  const [postMortem, setPostMortem] = useState<ApiProposalPostMortem | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  useEffect(() => {
    apiGetProposalPostMortem(proposalId)
      .then((data) => {
        setPostMortem(data);
        setForm({
          outcome: data.outcome,
          outcome_reason: data.outcome_reason || '',
          client_feedback: data.client_feedback || '',
          lessons_learned_text: (data.lessons_learned || []).join('\n'),
        });
      })
      .catch((err: unknown) => {
        // 404 = no post-mortem yet, show form directly
        const msg = err instanceof Error ? err.message : '';
        if (!msg.includes('404') && !msg.toLowerCase().includes('not found')) {
          setError('Erro ao carregar post-mortem.');
        }
        setEditing(true);
      })
      .finally(() => setLoading(false));
  }, [proposalId]);

  const handleSave = async () => {
    if (!form.outcome) return;
    setSaving(true);
    setError('');
    try {
      const lessons = form.lessons_learned_text
        .split('\n')
        .map((l) => l.trim())
        .filter(Boolean);
      const saved = await apiCreateProposalPostMortem(proposalId, {
        outcome: form.outcome,
        outcome_reason: form.outcome_reason || undefined,
        client_feedback: form.client_feedback || undefined,
        lessons_learned: lessons.length > 0 ? lessons : undefined,
      });
      setPostMortem(saved);
      setEditing(false);
    } catch {
      setError('Erro ao gravar post-mortem.');
    } finally {
      setSaving(false);
    }
  };

  const startEdit = () => {
    if (postMortem) {
      setForm({
        outcome: postMortem.outcome,
        outcome_reason: postMortem.outcome_reason || '',
        client_feedback: postMortem.client_feedback || '',
        lessons_learned_text: (postMortem.lessons_learned || []).join('\n'),
      });
    }
    setEditing(true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0 bg-muted/20">
        <div>
          <p className="text-xs font-semibold">Post-Mortem</p>
          <p className="text-[10px] text-muted-foreground">
            {loading ? 'A carregar...' : postMortem ? 'Registado' : 'Ainda não registado'}
          </p>
        </div>
        {postMortem && !editing && (
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1.5" onClick={startEdit}>
            <Edit2 className="h-3.5 w-3.5" />
            Editar
          </Button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-10 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      )}

      {!loading && (
        <div className="flex-1 overflow-auto px-4 py-3 space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
              <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Warning banner */}
          {editing && (
            <div className="flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 px-3 py-2">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-[10px] text-amber-700 leading-relaxed">
                Registar o outcome <strong>won</strong> ou <strong>lost</strong> pode atualizar automaticamente
                o estado da proposta. Não altera QC nem scores.
              </p>
            </div>
          )}

          {/* Read view */}
          {postMortem && !editing && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge
                  className={cn(
                    'text-xs',
                    OUTCOME_CONFIG[postMortem.outcome]?.color ?? 'bg-muted text-muted-foreground'
                  )}
                >
                  {OUTCOME_CONFIG[postMortem.outcome]?.label ?? postMortem.outcome}
                </Badge>
                {postMortem.sentiment && (
                  <Badge variant="outline" className="text-[10px]">
                    Sentimento: {postMortem.sentiment}
                  </Badge>
                )}
              </div>

              {postMortem.outcome_reason && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Razão do resultado
                  </p>
                  <p className="text-xs text-foreground leading-relaxed">{postMortem.outcome_reason}</p>
                </div>
              )}

              {postMortem.client_feedback && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Feedback do cliente
                  </p>
                  <p className="text-xs text-foreground leading-relaxed">{postMortem.client_feedback}</p>
                </div>
              )}

              {postMortem.lessons_learned && postMortem.lessons_learned.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Lições aprendidas
                  </p>
                  <ul className="space-y-1">
                    {postMortem.lessons_learned.map((lesson, i) => (
                      <li key={i} className="text-xs flex items-start gap-1.5">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                        {lesson}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {postMortem.created_by_detail && (
                <p className="text-[10px] text-muted-foreground">
                  Registado por:{' '}
                  {postMortem.created_by_detail.full_name || postMortem.created_by_detail.username}
                  {' · '}
                  {new Date(postMortem.created_at).toLocaleDateString('pt-PT')}
                </p>
              )}
            </div>
          )}

          {/* Edit / create form */}
          {editing && (
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                  Resultado *
                </label>
                <Select
                  value={form.outcome}
                  onValueChange={(v) =>
                    setForm((p) => ({ ...p, outcome: v as ApiProposalPostMortem['outcome'] }))
                  }
                >
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(OUTCOME_CONFIG).map(([value, cfg]) => (
                      <SelectItem key={value} value={value} className="text-xs">
                        {cfg.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                  Razão do resultado
                </label>
                <Textarea
                  className="text-xs min-h-[72px] resize-none"
                  placeholder="Porquê ganhámos / perdemos..."
                  value={form.outcome_reason}
                  onChange={(e) => setForm((p) => ({ ...p, outcome_reason: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                  Feedback do cliente
                </label>
                <Textarea
                  className="text-xs min-h-[60px] resize-none"
                  placeholder="O que o cliente comunicou..."
                  value={form.client_feedback}
                  onChange={(e) => setForm((p) => ({ ...p, client_feedback: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1">
                  Lições aprendidas
                </label>
                <p className="text-[10px] text-muted-foreground mb-1.5">
                  Uma lição por linha.
                </p>
                <Textarea
                  className="text-xs min-h-[80px] resize-none"
                  placeholder="Detalhar o processo de scoring...&#10;Incluir referências de projeto similar...&#10;..."
                  value={form.lessons_learned_text}
                  onChange={(e) => setForm((p) => ({ ...p, lessons_learned_text: e.target.value }))}
                />
              </div>

              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="h-7 text-xs flex-1"
                  onClick={handleSave}
                  disabled={saving || !form.outcome}
                >
                  {saving ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                  ) : (
                    <Save className="h-3.5 w-3.5 mr-1" />
                  )}
                  Gravar Post-Mortem
                </Button>
                {postMortem && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => setEditing(false)}
                  >
                    Cancelar
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!postMortem && !editing && !loading && (
            <div className="text-center py-10">
              <BookOpen className="h-8 w-8 mx-auto mb-2 text-muted-foreground/40" />
              <p className="text-xs text-muted-foreground">Nenhum post-mortem registado.</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 text-xs h-7"
                onClick={() => setEditing(true)}
              >
                Registar Post-Mortem
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
