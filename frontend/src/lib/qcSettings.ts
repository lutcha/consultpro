const QC_SETTINGS_KEY = 'consultpro.proposals.qcSettings';

export interface ProposalQCSettings {
  minScore: number;
}

export const DEFAULT_QC_SETTINGS: ProposalQCSettings = {
  minScore: 85,
};

export function readQCSettings(): ProposalQCSettings {
  try {
    const parsed = JSON.parse(localStorage.getItem(QC_SETTINGS_KEY) || '{}') as Partial<ProposalQCSettings>;
    const minScore = Number(parsed.minScore);
    return {
      minScore: Number.isFinite(minScore) ? Math.max(0, Math.min(100, minScore)) : DEFAULT_QC_SETTINGS.minScore,
    };
  } catch {
    return DEFAULT_QC_SETTINGS;
  }
}

export function writeQCSettings(settings: ProposalQCSettings) {
  localStorage.setItem(
    QC_SETTINGS_KEY,
    JSON.stringify({
      minScore: Math.max(0, Math.min(100, settings.minScore)),
    })
  );
}
