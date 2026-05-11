// ============================================
// REPORT PREVIEW — beautiful print-ready document
// ============================================

import { X, Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '@/lib/utils';
import type { DashboardStats, PipelineItem, FunnelData, DeadlineItem } from '@/types';
import type { User } from '@/types';

export type ReportPeriod = 'weekly' | 'monthly' | 'quarterly';

interface ReportPreviewProps {
  stats: DashboardStats;
  pipeline: PipelineItem[];
  funnel: FunnelData | null;
  user: User | null;
  period: ReportPeriod;
  onClose: () => void;
}

// ── Constants ────────────────────────────────────────────────────

const PERIOD_LABELS: Record<ReportPeriod, string> = {
  weekly: 'Semanal',
  monthly: 'Mensal',
  quarterly: 'Trimestral',
};

const STATUS_LABELS: Record<string, string> = {
  new: 'Novas',
  analyzing: 'Em Análise',
  go: 'Go',
  no_go: 'No-Go',
  proposal_draft: 'Rascunho',
  proposal_review: 'Revisão',
  submitted: 'Submetidas',
  won: 'Ganhas',
  lost: 'Perdidas',
  draft: 'Rascunho',
  in_review: 'Em Revisão',
  qc_check: 'QC Check',
  approved: 'Aprovada',
};

const STATUS_COLORS: Record<string, string> = {
  new: '#6366f1',
  analyzing: '#f59e0b',
  go: '#10b981',
  no_go: '#ef4444',
  proposal_draft: '#3b82f6',
  proposal_review: '#8b5cf6',
  submitted: '#06b6d4',
  won: '#10b981',
  lost: '#ef4444',
  draft: '#94a3b8',
  in_review: '#f59e0b',
  qc_check: '#8b5cf6',
  approved: '#10b981',
};

function getPeriodText(period: ReportPeriod): string {
  const now = new Date();
  const months = [
    'Janeiro','Fevereiro','Março','Abril','Maio','Junho',
    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro',
  ];
  if (period === 'weekly') {
    const from = new Date(now);
    from.setDate(now.getDate() - 6);
    return `${from.getDate()}–${now.getDate()} de ${months[now.getMonth()]} ${now.getFullYear()}`;
  }
  if (period === 'monthly') {
    return `${months[now.getMonth()]} ${now.getFullYear()}`;
  }
  const q = Math.floor(now.getMonth() / 3) + 1;
  const s = months[(q - 1) * 3];
  const e = months[Math.min((q - 1) * 3 + 2, 11)];
  return `Q${q} ${now.getFullYear()} — ${s} a ${e}`;
}

// ── Root component ───────────────────────────────────────────────

export function ReportPreview({ stats, pipeline, funnel, user, period, onClose }: ReportPreviewProps) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('pt-PT', { day: '2-digit', month: 'long', year: 'numeric' });
  const periodText = getPeriodText(period);

  const statusEntries = Object.entries(stats.opportunitiesByStatus || {});
  const totalOpps = statusEntries.reduce((s, [, v]) => s + v, 0);
  const topPipeline = pipeline.slice(0, 10);

  return (
    <>
      {/* Print-only CSS */}
      <style>{`
        @media print {
          body > * { visibility: hidden !important; }
          #rp-overlay, #rp-overlay * { visibility: visible !important; }
          #rp-overlay {
            position: fixed !important;
            inset: 0 !important;
            background: #ffffff !important;
            overflow: visible !important;
            padding: 0 !important;
          }
          .rp-controls { display: none !important; }
          .rp-page {
            box-shadow: none !important;
            border-radius: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
          }
          @page { size: A4; margin: 0; }
        }
      `}</style>

      {/* Full-screen overlay */}
      <div
        id="rp-overlay"
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(3, 7, 18, 0.9)',
          zIndex: 9999,
          overflowY: 'auto',
          padding: '20px 16px 40px',
        }}
      >
        {/* Sticky controls bar */}
        <div
          className="rp-controls"
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 10,
            display: 'flex',
            justifyContent: 'center',
            gap: '10px',
            marginBottom: '20px',
            paddingTop: '4px',
          }}
        >
          <Button
            onClick={() => window.print()}
            style={{
              background: 'linear-gradient(135deg, #0d9488, #3b82f6)',
              color: '#fff',
              border: 'none',
              padding: '8px 20px',
              fontWeight: 600,
              boxShadow: '0 4px 20px rgba(13,148,136,0.4)',
            }}
          >
            <Printer className="h-4 w-4 mr-2" />
            Imprimir / Exportar PDF
          </Button>
          <Button
            variant="ghost"
            onClick={onClose}
            style={{ color: 'rgba(255,255,255,0.7)', border: '1px solid rgba(255,255,255,0.15)' }}
          >
            <X className="h-4 w-4 mr-2" />
            Fechar
          </Button>
        </div>

        {/* ── Report page ────────────────────────────────────────── */}
        <div
          className="rp-page"
          style={{
            maxWidth: '794px',
            margin: '0 auto',
            background: '#ffffff',
            borderRadius: '16px',
            overflow: 'hidden',
            boxShadow: '0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06)',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif',
          }}
        >
          {/* ── HEADER ──────────────────────────────────────────── */}
          <div
            style={{
              background: 'linear-gradient(135deg, #0a0f1e 0%, #0f2040 40%, #0d3558 70%, #0a4a5c 100%)',
              padding: '44px 52px 40px',
              color: '#ffffff',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Decorative circles */}
            <div style={{ position:'absolute', top:-60, right:-40, width:220, height:220, background:'rgba(255,255,255,0.025)', borderRadius:'50%' }} />
            <div style={{ position:'absolute', bottom:-40, left:'40%', width:160, height:160, background:'rgba(13,148,136,0.1)', borderRadius:'50%' }} />
            <div style={{ position:'absolute', top:20, right:160, width:80, height:80, background:'rgba(59,130,246,0.12)', borderRadius:'50%' }} />

            {/* Teal accent line */}
            <div style={{ width:48, height:3, background:'linear-gradient(to right, #0d9488, #3b82f6)', borderRadius:2, marginBottom:28 }} />

            {/* Top row */}
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 }}>
              <div>
                <div style={{ fontSize:24, fontWeight:800, letterSpacing:'-0.5px', color:'#ffffff' }}>ConsultPro</div>
                <div style={{ fontSize:11, color:'rgba(255,255,255,0.45)', marginTop:3, letterSpacing:'1.5px', textTransform:'uppercase' }}>
                  Plataforma de Gestão de Propostas
                </div>
              </div>
              <div style={{
                background:'rgba(13,148,136,0.2)',
                border:'1px solid rgba(13,148,136,0.4)',
                borderRadius:6,
                padding:'5px 14px',
                fontSize:11,
                fontWeight:700,
                color:'#5eead4',
                letterSpacing:'1px',
                textTransform:'uppercase',
              }}>
                {PERIOD_LABELS[period]}
              </div>
            </div>

            {/* Title */}
            <h1 style={{ fontSize:32, fontWeight:900, margin:'0 0 6px', letterSpacing:'-1px', lineHeight:1.1 }}>
              Relatório de Performance
            </h1>
            <p style={{ fontSize:15, color:'rgba(255,255,255,0.6)', margin:0, fontWeight:400 }}>
              {periodText}
            </p>

            {/* Meta row */}
            <div style={{
              display:'flex', justifyContent:'space-between', alignItems:'center',
              marginTop:28, paddingTop:20,
              borderTop:'1px solid rgba(255,255,255,0.1)',
            }}>
              <div style={{ fontSize:13, color:'rgba(255,255,255,0.55)' }}>
                Gerado em{' '}
                <strong style={{ color:'rgba(255,255,255,0.85)' }}>{dateStr}</strong>
                {user && (
                  <>
                    {' '}· Por{' '}
                    <strong style={{ color:'rgba(255,255,255,0.85)' }}>{user.name}</strong>
                  </>
                )}
              </div>
              <div style={{
                fontSize:10,
                color:'rgba(255,255,255,0.3)',
                letterSpacing:'2px',
                textTransform:'uppercase',
              }}>
                Confidencial
              </div>
            </div>
          </div>

          {/* ── BODY ────────────────────────────────────────────── */}
          <div style={{ padding:'44px 52px' }}>

            {/* SECTION: Resumo Executivo */}
            <RpSectionTitle>Resumo Executivo</RpSectionTitle>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:14, marginBottom:14 }}>
              <RpMetric label="Oportunidades Ativas"  value={stats.activeOpportunities}    color="#6366f1" bg="#eef2ff" />
              <RpMetric label="Propostas em Curso"    value={stats.proposalsInProgress}    color="#0d9488" bg="#f0fdfa" />
              <RpMetric label="Taxa de Vitória"       value={`${stats.winRate}%`}           color="#10b981" bg="#ecfdf5" />
              <RpMetric label="Prazos ≤7 Dias"        value={stats.upcomingDeadlines}      color="#f59e0b" bg="#fffbeb" />
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:14, marginBottom:36 }}>
              <RpMetric label="Projetos Ativos"       value={stats.projectsActive}         color="#3b82f6" bg="#eff6ff"  small />
              <RpMetric label="Projetos Concluídos"   value={stats.projectsCompleted}      color="#10b981" bg="#ecfdf5"  small />
              <RpMetric label="Opors. Scraped"        value={stats.scrapingNew}            color="#8b5cf6" bg="#f5f3ff"  small />
              <RpMetric label="Com Análise IA"        value={stats.scrapingWithAI}         color="#06b6d4" bg="#ecfeff"  small />
            </div>

            <RpDivider />

            {/* SECTION: Funil + Financeiro */}
            {funnel && (
              <>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:28, marginBottom:36 }}>
                  <div>
                    <RpSectionTitle>Funil de Conversão</RpSectionTitle>
                    <RpFunnel funnel={funnel} />
                  </div>
                  <div>
                    <RpSectionTitle>Desempenho Financeiro</RpSectionTitle>
                    <RpFinancial funnel={funnel} />
                  </div>
                </div>
                <RpDivider />
              </>
            )}

            {/* SECTION: Pipeline */}
            {topPipeline.length > 0 && (
              <>
                <RpSectionTitle>Pipeline de Propostas — Top {topPipeline.length}</RpSectionTitle>
                <RpPipelineTable items={topPipeline} />
                <RpDivider />
              </>
            )}

            {/* SECTION: Status distribution */}
            {statusEntries.length > 0 && (
              <>
                <RpSectionTitle>Distribuição por Estado ({totalOpps} total)</RpSectionTitle>
                <RpStatusBars entries={statusEntries} total={totalOpps} />
              </>
            )}

            {/* SECTION: Upcoming deadlines */}
            {(stats.deadlineItems?.length ?? 0) > 0 && (
              <>
                <RpDivider />
                <RpSectionTitle>Prazos Urgentes</RpSectionTitle>
                <RpDeadlines items={stats.deadlineItems.slice(0, 5)} />
              </>
            )}
          </div>

          {/* ── FOOTER ──────────────────────────────────────────── */}
          <div style={{
            background:'#f8fafc',
            borderTop:'1px solid #e8edf3',
            padding:'14px 52px',
            display:'flex',
            justifyContent:'space-between',
            alignItems:'center',
          }}>
            <div style={{ fontSize:11, color:'#64748b' }}>
              <strong style={{ color:'#0f172a' }}>ConsultPro</strong> © {now.getFullYear()}
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:8 }}>
              <div style={{ width:4, height:4, borderRadius:'50%', background:'#cbd5e1' }} />
              <div style={{ fontSize:10, color:'#94a3b8', letterSpacing:'1px', textTransform:'uppercase' }}>Documento Confidencial</div>
              <div style={{ width:4, height:4, borderRadius:'50%', background:'#cbd5e1' }} />
            </div>
            <div style={{ fontSize:11, color:'#64748b' }}>
              {now.toLocaleDateString('pt-PT')}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ── Sub-components ───────────────────────────────────────────────

function RpSectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h2 style={{
        fontSize: 10,
        fontWeight: 800,
        letterSpacing: '2px',
        color: '#94a3b8',
        textTransform: 'uppercase',
        margin: '0 0 7px',
      }}>
        {children}
      </h2>
      <div style={{ height:2, width:28, background:'linear-gradient(to right, #0d9488, #3b82f6)', borderRadius:2 }} />
    </div>
  );
}

function RpDivider() {
  return (
    <div style={{
      margin: '28px 0',
      height: 1,
      background: 'linear-gradient(to right, transparent, #e2e8f0 20%, #e2e8f0 80%, transparent)',
    }} />
  );
}

function RpMetric({ label, value, color, bg, small }: {
  label: string; value: number | string; color: string; bg: string; small?: boolean;
}) {
  return (
    <div style={{
      background: bg,
      borderRadius: 10,
      padding: small ? '14px 16px' : '20px 18px',
      borderLeft: `3px solid ${color}`,
      position: 'relative',
    }}>
      <div style={{ fontSize: small ? 22 : 30, fontWeight: 900, color: '#0f172a', lineHeight: 1, letterSpacing: '-1px' }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: '#64748b', marginTop: 6, lineHeight: 1.4 }}>
        {label}
      </div>
      <div style={{
        position: 'absolute',
        top: 10, right: 12,
        width: 6, height: 6,
        borderRadius: '50%',
        background: color,
        opacity: 0.6,
      }} />
    </div>
  );
}

function RpFunnel({ funnel }: { funnel: FunnelData }) {
  const stages = [
    { label: 'Oportunidades Ativas', count: funnel.funnel.opportunities.count, color: '#6366f1', bg: '#eef2ff' },
    { label: 'Propostas Submetidas', count: funnel.funnel.proposals.count,     color: '#0d9488', bg: '#f0fdfa', sub: `${funnel.funnel.proposals.won} ganhas` },
    { label: 'Projetos em Carteira', count: funnel.funnel.projects.count,      color: '#10b981', bg: '#ecfdf5', sub: `${funnel.funnel.projects.active} ativos` },
  ];
  const rates = [funnel.conversion.oppToProposal, funnel.conversion.proposalToProject];

  return (
    <div>
      {/* Visual funnel bars (decreasing width) */}
      <div style={{ marginBottom: 16 }}>
        {stages.map((s, i) => {
          const widthPct = 100 - i * 18;
          return (
            <div key={s.label} style={{ marginBottom: 6 }}>
              <div style={{
                width: `${widthPct}%`,
                background: s.bg,
                borderLeft: `3px solid ${s.color}`,
                borderRadius: '0 6px 6px 0',
                padding: '10px 14px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                position: 'relative',
              }}>
                <div>
                  <span style={{ fontSize: 13, fontWeight: 700, color: s.color }}>{s.count}</span>
                  <span style={{ fontSize: 11, color: '#64748b', marginLeft: 8 }}>{s.label}</span>
                </div>
                {s.sub && (
                  <span style={{ fontSize: 10, color: '#10b981', fontWeight: 600 }}>{s.sub}</span>
                )}
              </div>
              {i < rates.length && (
                <div style={{ display:'flex', alignItems:'center', gap:6, padding:'3px 14px', opacity:0.8 }}>
                  <div style={{ width:1, height:12, background:'#cbd5e1', marginLeft:1 }} />
                  <span style={{ fontSize:10, color:'#64748b', fontWeight:700 }}>
                    {rates[i]}% de conversão
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RpFinancial({ funnel }: { funnel: FunnelData }) {
  const f = funnel.financial;
  const items = [
    { label: 'Pipeline',            value: f.pipelineValue,    color: '#6366f1', bg: '#eef2ff' },
    { label: 'Propostas Enviadas',  value: f.proposalsValue,   color: '#0d9488', bg: '#f0fdfa' },
    { label: 'Carteira em Exec.',   value: f.portfolioValue,   color: '#3b82f6', bg: '#eff6ff' },
    {
      label: 'Margem Estimada',
      value: f.estimatedMargin,
      color: f.estimatedMargin >= 0 ? '#10b981' : '#ef4444',
      bg:    f.estimatedMargin >= 0 ? '#ecfdf5' : '#fef2f2',
    },
  ];

  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
      {items.map((item) => (
        <div key={item.label} style={{
          background: item.bg,
          borderRadius: 10,
          padding: '14px 16px',
          borderLeft: `3px solid ${item.color}`,
        }}>
          <div style={{ fontSize: 10, color: '#64748b', marginBottom: 5, textTransform:'uppercase', letterSpacing:'0.5px' }}>
            {item.label}
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: item.color, letterSpacing: '-0.5px' }}>
            {formatCurrency(item.value, f.currency)}
          </div>
        </div>
      ))}
    </div>
  );
}

function RpPipelineTable({ items }: { items: PipelineItem[] }) {
  const cols = ['#', 'Título', 'Cliente', 'Estado', 'Valor', 'Prog.'];
  return (
    <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
      <thead>
        <tr>
          {cols.map((c) => (
            <th key={c} style={{
              padding: '7px 10px',
              textAlign: 'left',
              fontSize: 10,
              fontWeight: 700,
              color: '#94a3b8',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              background: '#f8fafc',
              borderBottom: '2px solid #e2e8f0',
            }}>{c}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((item, idx) => (
          <tr
            key={item.id}
            style={{ background: idx % 2 === 0 ? '#ffffff' : '#f8fafc', borderBottom: '1px solid #f1f5f9' }}
          >
            <td style={{ padding:'8px 10px', color:'#94a3b8', fontWeight:600, fontSize:11 }}>{idx + 1}</td>
            <td style={{ padding:'8px 10px', maxWidth:180 }}>
              <div style={{ fontWeight:500, color:'#0f172a', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {item.title}
              </div>
            </td>
            <td style={{ padding:'8px 10px', color:'#475569', whiteSpace:'nowrap' }}>{item.client}</td>
            <td style={{ padding:'8px 10px' }}>
              <span style={{
                background: (STATUS_COLORS[item.status] ?? '#94a3b8') + '22',
                color: STATUS_COLORS[item.status] ?? '#94a3b8',
                padding: '2px 8px',
                borderRadius: 4,
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: '0.3px',
              }}>
                {STATUS_LABELS[item.status] ?? item.status}
              </span>
            </td>
            <td style={{ padding:'8px 10px', fontWeight:700, color:'#0f172a', whiteSpace:'nowrap', fontSize:11 }}>
              {item.value ? formatCurrency(item.value, 'USD') : '—'}
            </td>
            <td style={{ padding:'8px 10px', minWidth:70 }}>
              {item.id.startsWith('proposal-') ? (
                <div style={{ display:'flex', alignItems:'center', gap:5 }}>
                  <div style={{ flex:1, height:4, background:'#e2e8f0', borderRadius:2, overflow:'hidden' }}>
                    <div style={{
                      height:'100%',
                      width:`${item.progress}%`,
                      background: item.progress >= 80 ? '#10b981' : item.progress >= 50 ? '#3b82f6' : '#f59e0b',
                      borderRadius:2,
                    }} />
                  </div>
                  <span style={{ fontSize:9, color:'#64748b', whiteSpace:'nowrap' }}>{item.progress}%</span>
                </div>
              ) : (
                <span style={{ color:'#cbd5e1', fontSize:11 }}>—</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RpStatusBars({ entries, total }: { entries: [string, number][]; total: number }) {
  const sorted = [...entries].sort(([, a], [, b]) => b - a);
  const max = sorted[0]?.[1] ?? 1;

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
      {sorted.map(([status, count]) => {
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        const barW = Math.round((count / max) * 100);
        const color = STATUS_COLORS[status] ?? '#94a3b8';
        return (
          <div key={status} style={{ display:'flex', alignItems:'center', gap:12 }}>
            <div style={{ width:96, fontSize:11, color:'#475569', flexShrink:0, fontWeight:500 }}>
              {STATUS_LABELS[status] ?? status}
            </div>
            <div style={{ flex:1, height:8, background:'#f1f5f9', borderRadius:4, overflow:'hidden' }}>
              <div style={{
                height:'100%',
                width:`${barW}%`,
                background: `linear-gradient(to right, ${color}, ${color}bb)`,
                borderRadius:4,
                minWidth: barW > 0 ? 6 : 0,
              }} />
            </div>
            <div style={{ width:22, fontSize:12, fontWeight:800, color:'#0f172a', textAlign:'right' }}>
              {count}
            </div>
            <div style={{ width:34, fontSize:10, color:'#94a3b8', textAlign:'right' }}>
              {pct}%
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RpDeadlines({ items }: { items: DeadlineItem[] }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
      {items.map((item) => {
        const urgent = item.daysLeft <= 1;
        const warning = item.daysLeft <= 3;
        const borderColor = urgent ? '#ef4444' : warning ? '#f59e0b' : '#e2e8f0';
        const bg = urgent ? '#fef2f2' : warning ? '#fffbeb' : '#f8fafc';
        return (
          <div key={item.id} style={{
            display:'flex', alignItems:'center', justifyContent:'space-between',
            padding:'10px 14px',
            background: bg,
            borderRadius: 8,
            borderLeft: `3px solid ${borderColor}`,
          }}>
            <div>
              <div style={{ fontSize:13, fontWeight:500, color:'#0f172a' }}>{item.title}</div>
              <div style={{ fontSize:11, color:'#64748b', marginTop:2 }}>{item.client}</div>
            </div>
            <div style={{
              fontSize:11, fontWeight:800,
              color: urgent ? '#ef4444' : warning ? '#f59e0b' : '#64748b',
              whiteSpace:'nowrap',
            }}>
              {item.daysLeft === 0 ? 'Hoje!' : item.daysLeft === 1 ? 'Amanhã' : `${item.daysLeft} dias`}
            </div>
          </div>
        );
      })}
    </div>
  );
}
