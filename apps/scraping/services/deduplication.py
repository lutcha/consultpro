"""
Deduplicação inteligente baseada em hash rápido + similaridade de texto.
Evita falsos positivos usando múltiplos fatores.
"""
import hashlib
import re
import logging
from difflib import SequenceMatcher
from datetime import timedelta
from typing import Tuple, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class SmartDeduplicator:
    """Deduplicação baseada em múltiplos fatores para evitar falsos positivos."""

    SIMILARITY_THRESHOLD = 0.82
    DEADLINE_TOLERANCE_HOURS = 72  # 3 dias de tolerância

    @classmethod
    def check_duplicate(
        cls,
        title: str,
        description: str,
        deadline: Optional[timezone.datetime],
        source_name: str,
        external_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[int]]:
        """
        Verifica se já existe uma oportunidade similar no sistema.
        Retorna: (is_duplicate, existing_scraped_opportunity_id)
        """
        from apps.scraping.models import ScrapedOpportunity

        # 1. Se tem external_id único, verificar exact match na mesma fonte
        if external_id:
            existing = ScrapedOpportunity.objects.filter(
                external_id=external_id,
                source__name=source_name,
            ).exclude(status='rejected').first()
            if existing:
                return True, existing.id

        # 2. Normalização e hash rápido
        title_normalized = cls._normalize_text(title)
        if not title_normalized:
            return False, None

        deadline_day = deadline.date() if deadline else None

        # 3. Buscar candidatos potenciais (mesmo dia de deadline, não rejeitados)
        candidates = ScrapedOpportunity.objects.filter(
            status__in=['new', 'imported', 'ignored', 'expired'],
        )

        if deadline_day:
            candidates = candidates.filter(deadline__date=deadline_day)

        # Limitar a candidatos recentes (últimos 90 dias) para performance
        recent_cutoff = timezone.now() - timedelta(days=90)
        candidates = (
            candidates
            .filter(scraped_at__gte=recent_cutoff)
            .only('id', 'title', 'description', 'deadline')
            .iterator(chunk_size=500)
        )

        for candidate in candidates:
            candidate_title_norm = cls._normalize_text(candidate.title)
            if not candidate_title_norm:
                continue

            # 4. Similaridade de título
            title_similarity = SequenceMatcher(
                None, title_normalized, candidate_title_norm
            ).ratio()

            if title_similarity >= cls.SIMILARITY_THRESHOLD:
                # 5. Segundo fator: descrição (primeiros 500 chars)
                desc_similarity = SequenceMatcher(
                    None,
                    cls._normalize_text(description[:500]),
                    cls._normalize_text(candidate.description[:500]),
                ).ratio()

                # 6. Terceiro fator: proximidade de prazos
                deadline_diff_hours = None
                if deadline and candidate.deadline:
                    deadline_diff_hours = abs(
                        (deadline - candidate.deadline).total_seconds()
                    ) / 3600

                # Decisão: título similar + descrição razoavelmente similar + prazo próximo
                if desc_similarity >= 0.65:
                    if deadline_diff_hours is None or deadline_diff_hours <= cls.DEADLINE_TOLERANCE_HOURS:
                        logger.info(
                            f"Duplicate detected: title_sim={title_similarity:.2f} "
                            f"desc_sim={desc_similarity:.2f} diff_h={deadline_diff_hours}"
                        )
                        return True, candidate.id

        return False, None

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normaliza texto para comparação."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @classmethod
    def compute_content_hash(cls, data: dict) -> str:
        """Computa hash SHA-256 para dados normalizados."""
        from json import dumps
        canonical = dumps(data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
