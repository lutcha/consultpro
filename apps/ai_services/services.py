import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseAIService:
    """Abstract base class for AI service implementations."""

    def analyze_document(self, text: str) -> dict:
        """Analyze a document and return summary, requirements, and risks.

        Returns:
            dict with keys: summary (str), requirements (list), risks (list)
        """
        raise NotImplementedError

    def generate_suggestion(self, section_type: str, content: str, action: str) -> str:
        """Generate a suggestion for a given section.

        Args:
            section_type: The type of section (e.g., 'scope', 'timeline', 'budget')
            content: The current content of the section
            action: The action to perform (e.g., 'expand', 'summarize', 'rewrite')

        Returns:
            Suggested text as a string
        """
        raise NotImplementedError

    def improve_text(self, content: str, action: str) -> str:
        """Improve the given text based on the action.

        Args:
            content: The text to improve
            action: The improvement action (e.g., 'clarity', 'tone', 'grammar')

        Returns:
            Improved text as a string
        """
        raise NotImplementedError


class OpenAIService(BaseAIService):
    """Concrete AI service implementation using the OpenAI API."""

    def __init__(self):
        import openai

        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def analyze_document(self, text: str) -> dict:
        system_prompt = (
            "You are an expert procurement analyst. Analyze the provided document "
            "and return a JSON object with exactly these keys:\n"
            "- summary: a concise summary of the document (string)\n"
            "- requirements: a list of key requirements (list of strings)\n"
            "- risks: a list of identified risks (list of strings)\n"
            "Respond with valid JSON only."
        )

        try:
            response = self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            return {
                'summary': result.get('summary', ''),
                'requirements': result.get('requirements', []),
                'risks': result.get('risks', []),
            }
        except Exception as exc:
            logger.exception('OpenAI analyze_document failed: %s', exc)
            return {
                'summary': '',
                'requirements': [],
                'risks': [],
            }

    def generate_suggestion(self, section_type: str, content: str, action: str) -> str:
        system_prompt = (
            "You are an expert proposal writer. Provide a helpful suggestion "
            "for the given section. Respond with plain text only."
        )
        user_prompt = (
            f"Section type: {section_type}\n"
            f"Action: {action}\n"
            f"Current content:\n{content}\n\n"
            f"Provide the improved suggestion."
        )

        try:
            response = self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.exception('OpenAI generate_suggestion failed: %s', exc)
            return ''

    def improve_text(self, content: str, action: str) -> str:
        system_prompt = (
            "You are an expert editor. Improve the provided text based on the "
            "requested action. Respond with the improved text only, no extra commentary."
        )
        user_prompt = (
            f"Action: {action}\n"
            f"Text:\n{content}\n\n"
            f"Provide the improved text."
        )

        try:
            response = self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.exception('OpenAI improve_text failed: %s', exc)
            return ''


class MockAIService(BaseAIService):
    """Mock AI service for development and testing.

    Returns realistic placeholder content when OpenAI is unavailable
    (quota exceeded, no API key, or AI_ALWAYS_MOCK=True).
    """

    def analyze_document(self, text: str) -> dict:
        logger.info('MockAIService.analyze_document called (len=%s)', len(text))
        return {
            'summary': (
                '[MOCK] This is a simulated summary of the document. '
                'The actual AI analysis is unavailable in development mode.'
            ),
            'requirements': [
                '[MOCK] Requirement 1: Demonstrate technical capability.',
                '[MOCK] Requirement 2: Provide past performance references.',
                '[MOCK] Requirement 3: Include detailed pricing breakdown.',
            ],
            'risks': [
                '[MOCK] Risk 1: Tight deadline may affect quality.',
                '[MOCK] Risk 2: Unclear evaluation criteria.',
            ],
        }

    def generate_suggestion(self, section_type: str, content: str, action: str) -> str:
        logger.info(
            'MockAIService.generate_suggestion called (section=%s, action=%s)',
            section_type, action,
        )
        suggestions = {
            'expand': (
                f'[MOCK — Expanded {section_type}]\n\n'
                f'This section has been expanded with additional detail. '
                f'Original content ({len(content)} chars) would be elaborated '
                f'with methodology, timelines, and deliverables. '
                f'Connect to the client\'s strategic objectives and quantify '
                f'expected outcomes wherever possible.'
            ),
            'summarize': (
                f'[MOCK — Summarized {section_type}]\n\n'
                f'Concise summary capturing the key points from the '
                f'original {len(content)} characters of content.'
            ),
            'rewrite': (
                f'[MOCK — Rewritten {section_type}]\n\n'
                f'This section has been rewritten for clarity and impact, '
                f'maintaining all original intent while improving readability.'
            ),
        }
        return suggestions.get(
            action,
            f'[MOCK — Suggestion for {section_type}]\n\n'
            f'Action requested: {action}. '
            f'Original content length: {len(content)} characters.',
        )

    def improve_text(self, content: str, action: str) -> str:
        logger.info(
            'MockAIService.improve_text called (action=%s, len=%s)',
            action, len(content),
        )
        improvements = {
            'clarity': (
                f'[MOCK — Improved for clarity]\n\n{content}\n\n'
                f'[The text above would be restructured for clearer '
                f'communication, shorter sentences, and active voice.]'
            ),
            'tone': (
                f'[MOCK — Tone adjusted]\n\n{content}\n\n'
                f'[The text above would be adjusted to a more professional '
                f'and confident tone suitable for a proposal context.]'
            ),
            'grammar': (
                f'[MOCK — Grammar corrected]\n\n{content}\n\n'
                f'[The text above would be checked for grammatical accuracy, '
                f'punctuation, and spelling.]'
            ),
        }
        return improvements.get(
            action,
            f'[MOCK — Text improved ({action})]\n\n{content}',
        )


class AIServiceFactory:
    """Factory for retrieving AI service instances.

    Attempts to use OpenAI first; falls back to MockAIService if:
      - OPENAI_API_KEY is missing or invalid
      - OpenAI API returns quota/authentication errors
      - AI_ALWAYS_MOCK=True in Django settings
    """

    _service = None

    @classmethod
    def get_service(cls) -> BaseAIService:
        if cls._service is None:
            cls._service = cls._create_service()
        return cls._service

    @classmethod
    def _create_service(cls) -> BaseAIService:
        if getattr(settings, 'AI_ALWAYS_MOCK', False):
            logger.info('AI_ALWAYS_MOCK=True — using MockAIService')
            return MockAIService()

        try:
            service = OpenAIService()
            logger.info('OpenAIService initialized successfully')
            return service
        except Exception as exc:
            logger.warning(
                'Failed to initialize OpenAIService (%s). '
                'Falling back to MockAIService. '
                'Set AI_ALWAYS_MOCK=True to suppress this warning.',
                exc,
            )
            return MockAIService()

    @classmethod
    def reset(cls):
        """Reset the cached service (useful in tests)."""
        cls._service = None
