"""
Determina se uma oportunidade é elegível para consultores em Cabo Verde.
Usa keywords geográficas, instituições de confiança e setores prioritários.
"""
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)


class CaboVerdeEligibilityValidator:
    """Determina se uma oportunidade é elegível para consultores em Cabo Verde."""

    POSITIVE_KEYWORDS_PT = [
        'cabo verde', 'cap-verde', 'cabo-verde', 'praia', 'mindelo', 'sal', 'santa maria',
        'boa vista', 'são vicente', 'santo antão', 'fogo', 'brava', 'maio', 'santiago',
        'palop', 'países de língua portuguesa', 'paises de lingua portuguesa',
        'lusófono', 'lusofono', 'africa ocidental', 'áfrica ocidental',
        'ecowas', 'cedeao', 'cplp', 'africa ocidental', 'west africa',
    ]

    POSITIVE_KEYWORDS_EN = [
        'cape verde', 'cap verde', 'cape-verde', 'west africa', 'lusophone africa',
        'lusophone', 'palop', 'ecowas', 'portuguese speaking', 'portuguese-speaking',
        'western africa', 'africa west',
    ]

    EXCLUSION_KEYWORDS = [
        'apenas brasil', 'only brazil', 'exclusivo portugal', 'only portugal',
        'américa latina', 'latin america only', 'sudeste asiático', 'southeast asia',
        'asia only', 'eastern europe only',
        'apenas angola', 'only mozambique', 'exclusively guine',
    ]

    TRUSTED_SOURCES_CV = [
        'ugpe.gov.cv',
        'instituto-camoes.pt',
        'aecid.es',
        'ecreee.org',
        'worldbank.org',
        'undp.org',
        'ecowas.int',
        'afdb.org',
        'fao.org',
        'unicef.org',
        'unops.org',
        'ungm.org',
        'imf.org',
        'eib.org',
        'afd.fr',
        'impactpool.org',
        'devex.com',
        'developmentbusiness.worldbank.org',
        'luxdev.lu',
    ]

    CV_PRIORITY_SECTORS = [
        'economia_azul', 'blue_economy', 'pescas', 'fisheries',
        'energias_renovaveis', 'renewable_energy', 'energy',
        'digitalizacao', 'digital', 'govtech', 'ict',
        'turismo', 'tourism',
        'gestao_agua', 'water_management', 'wASH',
        'saude_publica', 'health', 'one health',
        'igualdade_genero', 'gender', 'women empowerment',
        'infraestrutura', 'infrastructure',
        'agricultura', 'agriculture',
        'educacao', 'education',
        'governanca', 'governance',
    ]

    @classmethod
    def evaluate(cls, opportunity_data: Dict) -> Dict:
        """
        Avalia elegibilidade para Cabo Verde.
        Retorna: {is_eligible: bool, confidence: float, reasons: list, negative_reasons: list, metadata: dict}
        """
        reasons: List[str] = []
        negative_reasons: List[str] = []
        confidence_score = 0.0

        # 1. Verificação por fonte confiável
        source_url = opportunity_data.get('original_url', opportunity_data.get('external_url', '')).lower()
        source_name = opportunity_data.get('source_name', '')

        if any(trusted in source_url for trusted in cls.TRUSTED_SOURCES_CV):
            confidence_score += 0.35
            reasons.append('trusted_source_cabo_verde')

        # 2. Análise de texto (título + descrição + requisitos)
        text_parts = [
            opportunity_data.get('title', ''),
            opportunity_data.get('description', ''),
        ]
        if isinstance(opportunity_data.get('requirements'), list):
            text_parts.extend(str(r) for r in opportunity_data['requirements'])
        elif isinstance(opportunity_data.get('requirements'), str):
            text_parts.append(opportunity_data['requirements'])

        text_content = ' '.join(text_parts).lower()

        # Keywords positivas
        pt_matches = sum(1 for kw in cls.POSITIVE_KEYWORDS_PT if kw in text_content)
        en_matches = sum(1 for kw in cls.POSITIVE_KEYWORDS_EN if kw in text_content)
        total_geo_matches = pt_matches + en_matches

        if total_geo_matches > 0:
            confidence_score += min(0.35, total_geo_matches * 0.08)
            reasons.append(f'geographic_keywords_match_{total_geo_matches}')

        # Keywords de exclusão
        exclusion_hits = [excl for excl in cls.EXCLUSION_KEYWORDS if excl in text_content]
        if exclusion_hits:
            negative_reasons.append('geographic_exclusion_detected')
            confidence_score -= 0.4

        # 3. Verificação de idioma
        language = opportunity_data.get('language', 'unknown').lower()
        if language in ['pt', 'en', 'pt-br', 'pt-pt', 'eng', 'english', 'portuguese']:
            confidence_score += 0.1
            reasons.append('language_accessible')

        # 4. Setores prioritários para Cabo Verde
        sector_tags = opportunity_data.get('sector_tags', [])
        if not sector_tags and opportunity_data.get('sector'):
            sector_tags = [opportunity_data['sector']]
        sector_tags = [s.lower().replace(' ', '_') for s in sector_tags if s]

        priority_hits = [s for s in sector_tags if any(ps in s for ps in cls.CV_PRIORITY_SECTORS)]
        if priority_hits:
            confidence_score += min(0.15, len(priority_hits) * 0.05)
            reasons.append('priority_sector_for_cv')

        # 5. Heurística de tamanho/confiança
        if len(text_content) < 50:
            confidence_score -= 0.1
            negative_reasons.append('insufficient_description')

        # Decisão final
        is_eligible = confidence_score >= 0.25 and len(negative_reasons) == 0

        return {
            'is_eligible': is_eligible,
            'confidence': round(max(0.0, min(1.0, confidence_score)), 2),
            'reasons': reasons,
            'negative_reasons': negative_reasons,
            'metadata': {
                'source_trusted': any(trusted in source_url for trusted in cls.TRUSTED_SOURCES_CV),
                'keyword_matches_pt': pt_matches,
                'keyword_matches_en': en_matches,
                'language': language,
                'priority_sector_match': bool(priority_hits),
                'text_length': len(text_content),
            }
        }
