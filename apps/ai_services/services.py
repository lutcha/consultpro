import json
import logging

import openai
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseAIService:
    """Abstract base class for AI service implementations."""

    PROVIDER_NAME = 'base'

    def analyze_document(self, text: str) -> dict:
        """Analyze a document and return summary, requirements, and risks."""
        raise NotImplementedError

    def generate_suggestion(self, section_type: str, content: str, action: str) -> str:
        """Generate a suggestion for a given section."""
        raise NotImplementedError

    def improve_text(self, content: str, action: str) -> str:
        """Improve the given text based on the action."""
        raise NotImplementedError

    def _clean_json_response(self, content: str) -> str:
        """Strip markdown code fences that some providers wrap JSON in."""
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        return content.strip()


class LLMService(BaseAIService):
    """
    Generic LLM service for any OpenAI-compatible provider.

    Supports OpenAI, DeepSeek, Moonshot AI (Kimi), Qwen, Google Gemini,
    and any other provider that uses the OpenAI chat completions API format.
    """

    PROVIDER_NAME = 'generic'

    def __init__(self, api_key: str, base_url: str | None, model: str, provider_name: str = 'generic'):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.PROVIDER_NAME = provider_name

    def _chat_completion(self, messages: list, temperature: float = 0.5, json_mode: bool = False) -> str:
        """Internal helper for chat completions."""
        kwargs = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
        }
        if json_mode:
            kwargs['response_format'] = {'type': 'json_object'}

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ''
        except Exception as exc:
            if json_mode and 'response_format' in kwargs:
                logger.warning(
                    '%s rejected JSON response_format, retrying without it: %s',
                    self.PROVIDER_NAME,
                    exc,
                )
                kwargs.pop('response_format', None)
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ''
            logger.exception('%s chat completion failed: %s', self.PROVIDER_NAME, exc)
            raise

    def analyze_document(self, text: str) -> dict:
        system_prompt = (
            "You are a senior procurement and proposal architect for international consulting bids. "
            "Analyze the ToR using a proposal dissection methodology: identify the client, objective, "
            "scope, deliverables, eligibility, team requirements, methodology expectations, evaluation "
            "criteria, submission requirements, deadline pressure, compliance gaps, and proposal risks. "
            "Return valid JSON only with exactly these keys:\n"
            "- summary: Portuguese executive summary, max 500 words.\n"
            "- requirements: array of objects with description, category, priority. category must be one "
            "of functional, technical, institutional, financial. priority must be mandatory, preferred, optional.\n"
            "- risks: array of objects with description, severity, mitigation. severity must be low, medium, high.\n"
            "Extract specific actionable items. Do not invent facts that are not supported by the ToR."
        )

        try:
            content = self._chat_completion(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text},
                ],
                temperature=0.2,
                json_mode=True,
            )
            content = self._clean_json_response(content)
            result = json.loads(content)
            return {
                'summary': result.get('summary', ''),
                'requirements': result.get('requirements', []),
                'risks': result.get('risks', []),
            }
        except Exception as exc:
            logger.exception('%s analyze_document failed: %s', self.PROVIDER_NAME, exc)
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
            return self._chat_completion(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.7,
            ).strip()
        except Exception as exc:
            logger.exception('%s generate_suggestion failed: %s', self.PROVIDER_NAME, exc)
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
            return self._chat_completion(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.5,
            ).strip()
        except Exception as exc:
            logger.exception('%s improve_text failed: %s', self.PROVIDER_NAME, exc)
            return ''


class AnthropicService(BaseAIService):
    """
    Anthropic Claude service using the native Anthropic SDK.

    Claude uses a different API format than OpenAI (Messages API).
    This adapter normalizes it to the same BaseAIService interface.
    """

    PROVIDER_NAME = 'anthropic'

    def __init__(self, api_key: str, model: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _messages_create(self, system_prompt: str, user_prompt: str, temperature: float = 0.5) -> str:
        """Internal helper for Anthropic Messages API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {'role': 'user', 'content': user_prompt},
                ],
            )
            if response.content and len(response.content) > 0:
                return response.content[0].text or ''
            return ''
        except Exception as exc:
            logger.exception('Anthropic messages.create failed: %s', exc)
            raise

    def analyze_document(self, text: str) -> dict:
        system_prompt = (
            "You are a senior procurement and proposal architect for international consulting bids. "
            "Analyze the ToR using a proposal dissection methodology: identify the client, objective, "
            "scope, deliverables, eligibility, team requirements, methodology expectations, evaluation "
            "criteria, submission requirements, deadline pressure, compliance gaps, and proposal risks. "
            "Return valid JSON only with exactly these keys:\n"
            "- summary: Portuguese executive summary, max 500 words.\n"
            "- requirements: array of objects with description, category, priority. category must be one "
            "of functional, technical, institutional, financial. priority must be mandatory, preferred, optional.\n"
            "- risks: array of objects with description, severity, mitigation. severity must be low, medium, high.\n"
            "Extract specific actionable items. Do not invent facts that are not supported by the ToR. "
            "Do not wrap in markdown code blocks."
        )

        try:
            content = self._messages_create(
                system_prompt=system_prompt,
                user_prompt=text,
                temperature=0.2,
            )
            content = self._clean_json_response(content)
            result = json.loads(content)
            return {
                'summary': result.get('summary', ''),
                'requirements': result.get('requirements', []),
                'risks': result.get('risks', []),
            }
        except Exception as exc:
            logger.exception('Anthropic analyze_document failed: %s', exc)
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
            return self._messages_create(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            ).strip()
        except Exception as exc:
            logger.exception('Anthropic generate_suggestion failed: %s', exc)
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
            return self._messages_create(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
            ).strip()
        except Exception as exc:
            logger.exception('Anthropic improve_text failed: %s', exc)
            return ''


# Backwards compatibility: OpenAIService is now an alias for LLMService with OpenAI defaults
class OpenAIService(LLMService):
    """Legacy alias. Use AIServiceFactory instead."""

    def __init__(self):
        super().__init__(
            api_key=settings.OPENAI_API_KEY,
            base_url=None,
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
            provider_name='openai',
        )


class MockAIService(BaseAIService):
    """Mock AI service for development and testing."""

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
                f'Connect to the client strategic objectives and quantify '
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

    Provider selection priority:
      1. AI_PROVIDER setting
      2. AI_ALWAYS_MOCK=True -> MockAIService
      3. Fallback to mock if configured provider fails

    Valid providers: openai, deepseek, kimi, anthropic, qwen, google, mock
    """

    _service = None

    # OpenAI-compatible providers
    PROVIDER_REGISTRY = {
        'openai': {
            'api_key_setting': 'OPENAI_API_KEY',
            'base_url': None,
            'default_model': 'gpt-4o-mini',
            'model_setting': 'OPENAI_MODEL',
            'service_class': LLMService,
        },
        'deepseek': {
            'api_key_setting': 'DEEPSEEK_API_KEY',
            'base_url': 'https://api.deepseek.com',
            'default_model': 'deepseek-chat',
            'model_setting': 'DEEPSEEK_MODEL',
            'service_class': LLMService,
        },
        'kimi': {
            'api_key_setting': 'KIMI_API_KEY',
            'base_url': 'https://api.moonshot.cn/v1',
            'default_model': 'moonshot-v1-128k',
            'model_setting': 'KIMI_MODEL',
            'service_class': LLMService,
        },
        'qwen': {
            'api_key_setting': 'QWEN_API_KEY',
            'base_url': 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1',
            'default_model': 'qwen-max',
            'model_setting': 'QWEN_MODEL',
            'service_class': LLMService,
        },
        'google': {
            'api_key_setting': 'GOOGLE_API_KEY',
            'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
            'default_model': 'gemini-2.0-flash',
            'model_setting': 'GOOGLE_MODEL',
            'service_class': LLMService,
        },
    }

    # Native SDK providers (not OpenAI-compatible)
    NATIVE_PROVIDERS = {
        'anthropic': {
            'api_key_setting': 'ANTHROPIC_API_KEY',
            'default_model': 'claude-3-5-haiku-20241022',
            'model_setting': 'ANTHROPIC_MODEL',
            'service_class': AnthropicService,
        },
    }

    @classmethod
    def get_service(cls) -> BaseAIService:
        if cls._service is None:
            cls._service = cls._create_service()
        return cls._service

    @classmethod
    def get_provider_info(cls) -> dict:
        """Return info about the currently active provider."""
        service = cls.get_service()
        return {
            'provider': getattr(service, 'PROVIDER_NAME', 'unknown'),
            'model': getattr(service, 'model', 'unknown') if hasattr(service, 'model') else 'n/a',
            'is_mock': isinstance(service, MockAIService),
        }

    @classmethod
    def list_available_providers(cls) -> list:
        """Return a list of all valid provider names."""
        return (
            list(cls.PROVIDER_REGISTRY.keys())
            + list(cls.NATIVE_PROVIDERS.keys())
            + ['mock']
        )

    @classmethod
    def _create_service(cls) -> BaseAIService:
        if getattr(settings, 'AI_ALWAYS_MOCK', False):
            logger.info('AI_ALWAYS_MOCK=True using MockAIService')
            return MockAIService()

        provider = getattr(settings, 'AI_PROVIDER', 'openai').lower().strip()

        if provider == 'mock':
            return MockAIService()

        if provider in cls.NATIVE_PROVIDERS:
            return cls._create_native_service(provider)

        if provider in cls.PROVIDER_REGISTRY:
            return cls._create_openai_compatible_service(provider)

        logger.warning(
            "Unknown AI_PROVIDER '%s'. Falling back to MockAIService. "
            "Valid options: %s",
            provider,
            ', '.join(cls.list_available_providers()),
        )
        return MockAIService()

    @classmethod
    def _create_native_service(cls, provider: str) -> BaseAIService:
        config = cls.NATIVE_PROVIDERS[provider]
        api_key = getattr(settings, config['api_key_setting'], '') or ''

        if not api_key:
            logger.warning(
                "%s is not set. Falling back to MockAIService. "
                "Set %s in your environment or switch AI_PROVIDER.",
                config['api_key_setting'],
                config['api_key_setting'],
            )
            return MockAIService()

        model = getattr(settings, config['model_setting'], '') or config['default_model']
        service_class = config['service_class']

        try:
            service = service_class(api_key=api_key, model=model)
            logger.info('%s service initialized (model=%s)', provider, model)
            return service
        except Exception as exc:
            logger.exception(
                'Failed to initialize %s service. Falling back to MockAIService.',
                provider,
            )
            return MockAIService()

    @classmethod
    def _create_openai_compatible_service(cls, provider: str) -> BaseAIService:
        config = cls.PROVIDER_REGISTRY[provider]
        api_key = getattr(settings, config['api_key_setting'], '') or ''

        if not api_key:
            logger.warning(
                "%s is not set. Falling back to MockAIService. "
                "Set %s in your environment or switch AI_PROVIDER.",
                config['api_key_setting'],
                config['api_key_setting'],
            )
            return MockAIService()

        model = getattr(settings, config['model_setting'], '') or config['default_model']
        base_url = config['base_url']
        service_class = config['service_class']

        try:
            service = service_class(
                api_key=api_key,
                base_url=base_url,
                model=model,
                provider_name=provider,
            )
            logger.info(
                '%s LLMService initialized (model=%s, base_url=%s)',
                provider, model, base_url or 'default',
            )
            return service
        except Exception as exc:
            logger.exception(
                'Failed to initialize %s LLMService. Falling back to MockAIService.',
                provider,
            )
            return MockAIService()

    @classmethod
    def reset(cls):
        """Reset the cached service (useful in tests or when switching providers)."""
        cls._service = None
        logger.info('AIServiceFactory reset - next call will recreate service')

    @classmethod
    def switch_provider(cls, provider: str) -> BaseAIService:
        """Switch to a different provider at runtime (useful for admin panels)."""
        cls.reset()
        original = getattr(settings, 'AI_PROVIDER', None)
        settings.AI_PROVIDER = provider
        try:
            return cls.get_service()
        finally:
            if original is not None:
                settings.AI_PROVIDER = original
            else:
                delattr(settings, 'AI_PROVIDER')
