import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.ai_services.services import (
    AIServiceFactory,
    AnthropicService,
    BaseAIService,
    LLMService,
    MockAIService,
    OpenAIService,
)


class BaseAIServiceTests(TestCase):
    def test_analyze_document_not_implemented(self):
        class DummyService(BaseAIService):
            pass

        service = DummyService()
        with self.assertRaises(NotImplementedError):
            service.analyze_document('some text')

    def test_generate_suggestion_not_implemented(self):
        class DummyService(BaseAIService):
            pass

        service = DummyService()
        with self.assertRaises(NotImplementedError):
            service.generate_suggestion('scope', 'content', 'expand')

    def test_improve_text_not_implemented(self):
        class DummyService(BaseAIService):
            pass

        service = DummyService()
        with self.assertRaises(NotImplementedError):
            service.improve_text('content', 'clarity')


@override_settings(OPENAI_API_KEY='test-key')
class OpenAIServiceTests(TestCase):
    def setUp(self):
        self.service = OpenAIService()

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_analyze_document_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                'summary': 'Test summary',
                'requirements': ['Req 1', 'Req 2'],
                'risks': ['Risk 1'],
            })))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService()
        result = service.analyze_document('Sample document text')

        self.assertEqual(result['summary'], 'Test summary')
        self.assertEqual(result['requirements'], ['Req 1', 'Req 2'])
        self.assertEqual(result['risks'], ['Risk 1'])
        mock_client.chat.completions.create.assert_called_once()

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_analyze_document_failure_returns_empty(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception('API error')

        service = OpenAIService()
        result = service.analyze_document('Sample document text')

        self.assertEqual(result, {
            'summary': '',
            'requirements': [],
            'risks': [],
        })

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_generate_suggestion_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='  Suggested text  '))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService()
        result = service.generate_suggestion('scope', 'current content', 'expand')

        self.assertEqual(result, 'Suggested text')

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_generate_suggestion_failure_returns_empty(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception('API error')

        service = OpenAIService()
        result = service.generate_suggestion('scope', 'current content', 'expand')

        self.assertEqual(result, '')

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_improve_text_success(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='  Improved text  '))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService()
        result = service.improve_text('some text', 'clarity')

        self.assertEqual(result, 'Improved text')

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_improve_text_failure_returns_empty(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception('API error')

        service = OpenAIService()
        result = service.improve_text('some text', 'clarity')

        self.assertEqual(result, '')


class AIServiceFactoryTests(TestCase):
    def setUp(self):
        AIServiceFactory._service = None

    def tearDown(self):
        AIServiceFactory._service = None

    @override_settings(AI_PROVIDER='openai', AI_ALWAYS_MOCK=False, OPENAI_API_KEY='test-openai')
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_get_service_returns_openai_compatible_service(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        service = AIServiceFactory.get_service()
        self.assertIsInstance(service, LLMService)
        self.assertEqual(service.PROVIDER_NAME, 'openai')
        self.assertEqual(service.model, 'gpt-4o-mini')
        mock_openai_class.assert_called_once_with(api_key='test-openai', base_url=None)

    @override_settings(AI_PROVIDER='openai', AI_ALWAYS_MOCK=False, OPENAI_API_KEY='test-key')
    def test_get_service_singleton(self):
        with patch('apps.ai_services.services.openai.OpenAI') as mock_openai_class:
            mock_openai_class.return_value = MagicMock()
            service1 = AIServiceFactory.get_service()
            service2 = AIServiceFactory.get_service()
            self.assertIs(service1, service2)

    def test_list_available_providers(self):
        self.assertEqual(
            AIServiceFactory.list_available_providers(),
            ['openai', 'deepseek', 'kimi', 'qwen', 'google', 'anthropic', 'mock'],
        )

    @override_settings(AI_PROVIDER='mock', AI_ALWAYS_MOCK=False)
    def test_get_service_returns_mock_provider(self):
        service = AIServiceFactory.get_service()
        self.assertIsInstance(service, MockAIService)

    @override_settings(AI_PROVIDER='deepseek', AI_ALWAYS_MOCK=False, DEEPSEEK_API_KEY='')
    def test_missing_key_falls_back_to_mock(self):
        service = AIServiceFactory.get_service()
        self.assertIsInstance(service, MockAIService)

    @override_settings(AI_PROVIDER='unknown', AI_ALWAYS_MOCK=False)
    def test_unknown_provider_falls_back_to_mock(self):
        service = AIServiceFactory.get_service()
        self.assertIsInstance(service, MockAIService)

    @override_settings(AI_ALWAYS_MOCK=True, AI_PROVIDER='openai', OPENAI_API_KEY='test-openai')
    def test_ai_always_mock_overrides_provider(self):
        service = AIServiceFactory.get_service()
        self.assertIsInstance(service, MockAIService)

    @override_settings(AI_PROVIDER='deepseek', AI_ALWAYS_MOCK=False, DEEPSEEK_API_KEY='test-deepseek')
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_deepseek_provider_configuration(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        service = AIServiceFactory.get_service()
        self.assertEqual(service.PROVIDER_NAME, 'deepseek')
        self.assertEqual(service.model, 'deepseek-chat')
        mock_openai_class.assert_called_once_with(
            api_key='test-deepseek',
            base_url='https://api.deepseek.com',
        )

    @override_settings(AI_PROVIDER='kimi', AI_ALWAYS_MOCK=False, KIMI_API_KEY='test-kimi')
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_kimi_provider_configuration(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        service = AIServiceFactory.get_service()
        self.assertEqual(service.PROVIDER_NAME, 'kimi')
        self.assertEqual(service.model, 'moonshot-v1-128k')
        mock_openai_class.assert_called_once_with(
            api_key='test-kimi',
            base_url='https://api.moonshot.cn/v1',
        )

    @override_settings(AI_PROVIDER='qwen', AI_ALWAYS_MOCK=False, QWEN_API_KEY='test-qwen')
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_qwen_provider_configuration(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        service = AIServiceFactory.get_service()
        self.assertEqual(service.PROVIDER_NAME, 'qwen')
        self.assertEqual(service.model, 'qwen-max')
        mock_openai_class.assert_called_once_with(
            api_key='test-qwen',
            base_url='https://dashscope-intl.aliyuncs.com/compatible-mode/v1',
        )

    @override_settings(AI_PROVIDER='google', AI_ALWAYS_MOCK=False, GOOGLE_API_KEY='test-google')
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_google_provider_configuration(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        service = AIServiceFactory.get_service()
        self.assertEqual(service.PROVIDER_NAME, 'google')
        self.assertEqual(service.model, 'gemini-2.0-flash')
        mock_openai_class.assert_called_once_with(
            api_key='test-google',
            base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
        )

    @override_settings(AI_PROVIDER='anthropic', AI_ALWAYS_MOCK=False, ANTHROPIC_API_KEY='test-anthropic')
    def test_anthropic_provider_configuration(self):
        anthropic_module = SimpleNamespace(Anthropic=MagicMock(return_value=MagicMock()))
        with patch.dict(sys.modules, {'anthropic': anthropic_module}):
            service = AIServiceFactory.get_service()

        self.assertIsInstance(service, AnthropicService)
        self.assertEqual(service.PROVIDER_NAME, 'anthropic')
        self.assertEqual(service.model, 'claude-3-5-haiku-20241022')
        anthropic_module.Anthropic.assert_called_once_with(api_key='test-anthropic')

    @override_settings(AI_PROVIDER='deepseek', AI_ALWAYS_MOCK=False, DEEPSEEK_API_KEY='test-deepseek')
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_get_provider_info(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        info = AIServiceFactory.get_provider_info()
        self.assertEqual(info, {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'is_mock': False,
        })

    @override_settings(AI_PROVIDER='mock', AI_ALWAYS_MOCK=False)
    def test_build_prompt_metadata(self):
        metadata = AIServiceFactory.build_prompt_metadata('abcd' * 20)

        self.assertEqual(metadata['provider'], 'mock')
        self.assertTrue(metadata['is_mock'])
        self.assertEqual(metadata['prompt_chars'], 80)
        self.assertEqual(metadata['estimated_prompt_tokens'], 20)
        self.assertEqual(len(metadata['prompt_hash']), 64)


class LLMServiceTests(TestCase):
    @patch('apps.ai_services.services.openai.OpenAI')
    def test_json_mode_retries_without_response_format_when_provider_rejects_it(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                'summary': 'Summary',
                'requirements': [],
                'risks': [],
            })))
        ]
        mock_client.chat.completions.create.side_effect = [
            Exception('unsupported response_format'),
            mock_response,
        ]

        service = LLMService(
            api_key='test-key',
            base_url='https://example.com',
            model='test-model',
            provider_name='test-provider',
        )
        result = service.analyze_document('Text')

        self.assertEqual(result['summary'], 'Summary')
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
        first_call = mock_client.chat.completions.create.call_args_list[0].kwargs
        second_call = mock_client.chat.completions.create.call_args_list[1].kwargs
        self.assertIn('response_format', first_call)
        self.assertNotIn('response_format', second_call)
