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


class AIServiceFactory:
    """Factory for retrieving AI service instances."""

    _service = None

    @classmethod
    def get_service(cls) -> BaseAIService:
        if cls._service is None:
            cls._service = OpenAIService()
        return cls._service
