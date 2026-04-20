import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.ai_services.services import AIServiceFactory, BaseAIService, OpenAIService


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
    def tearDown(self):
        AIServiceFactory._service = None

    @patch('apps.ai_services.services.openai.OpenAI')
    def test_get_service_returns_openai_service(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        service = AIServiceFactory.get_service()
        self.assertIsInstance(service, OpenAIService)

    def test_get_service_singleton(self):
        with patch('apps.ai_services.services.openai.OpenAI') as mock_openai_class:
            mock_openai_class.return_value = MagicMock()
            service1 = AIServiceFactory.get_service()
            service2 = AIServiceFactory.get_service()
            self.assertIs(service1, service2)
