"""
Validação robusta de prazos de candidatura.
Normaliza timezones para Atlantic/Cape_Verde e detecta inconsistências.
"""
from datetime import datetime, timedelta
from typing import Optional
import re
import logging

from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class DeadlineValidator:
    """Validação robusta de prazos de candidatura."""

    MIN_DEADLINE_HOURS = 24  # Prazo mínimo aceitável
    MAX_DEADLINE_YEARS = 5   # Prazo máximo razoável
    DEFAULT_TZ = "Atlantic/Cape_Verde"
    DEFAULT_TZ_OFFSET = -1   # Cape Verde é UTC-1

    @classmethod
    def validate(
        cls,
        raw_deadline: str,
        published_at: Optional[datetime] = None,
        reference_now: Optional[datetime] = None
    ) -> dict:
        """
        Valida e normaliza um prazo de candidatura.
        Retorna dict com: is_valid, normalized_deadline, warnings, errors, metadata
        """
        result = {
            'is_valid': False,
            'normalized_deadline': None,
            'warnings': [],
            'errors': [],
            'metadata': {},
        }

        if not raw_deadline:
            result['errors'].append('deadline_missing')
            return result

        # 1. Parsing da data
        try:
            parsed = date_parser.parse(raw_deadline, fuzzy=True)
        except (ValueError, TypeError, OverflowError) as e:
            result['errors'].append(f'parse_error: {str(e)}')
            return result

        # 2. Normalização para timezone de Cabo Verde (ou UTC se não especificado)
        from datetime import timezone as dt_timezone
        if parsed.tzinfo is None:
            # Sem timezone: assumir UTC e depois ajustar para CV
            parsed = parsed.replace(tzinfo=dt_timezone.utc)
            result['warnings'].append('timezone_assumed_utc')

        # Converter para timezone de CV
        from django.utils import timezone as django_tz
        try:
            import zoneinfo
            cv_tz = zoneinfo.ZoneInfo(cls.DEFAULT_TZ)
            parsed = parsed.astimezone(cv_tz)
        except Exception:
            # Fallback: manter em UTC
            parsed = parsed.astimezone(dt_timezone.utc)

        # 3. Validação de coerência temporal
        now = reference_now or django_tz.now()

        if published_at and parsed < published_at:
            result['errors'].append('deadline_before_publication')
            return result

        if parsed < now:
            result['warnings'].append('deadline_already_passed')
            result['is_expired'] = True
        elif parsed < now + timedelta(hours=cls.MIN_DEADLINE_HOURS):
            result['warnings'].append('deadline_very_short')

        if parsed > now + timedelta(days=cls.MAX_DEADLINE_YEARS * 365):
            result['errors'].append('deadline_unreasonably_far')
            return result

        # 4. Extração de padrões específicos
        result['metadata'] = cls._extract_deadline_patterns(raw_deadline)

        # 5. Aprovação final
        if not result['errors']:
            result['is_valid'] = True
            result['normalized_deadline'] = parsed.isoformat()

        return result

    @classmethod
    def _extract_deadline_patterns(cls, raw: str) -> dict:
        """Extrai padrões úteis do texto original do prazo."""
        text = str(raw).strip()
        return {
            'has_time_specification': bool(re.search(r'\d{1,2}:\d{2}', text)),
            'mentions_timezone': bool(re.search(r'(GMT|UTC|WAT|CVT|local time|hora local)', text, re.I)),
            'relative_deadline': bool(re.search(r'(days?|weeks?|months?)\s+(from|after)', text, re.I)),
            'original_text': text,
        }
