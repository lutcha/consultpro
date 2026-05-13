from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.scraping.services.deep_extraction import extract_deep_content


class DeepExtractionTests(SimpleTestCase):
    @patch('apps.scraping.services.deep_extraction.requests.get')
    def test_extracts_readable_html_text(self, mock_get):
        response = Mock()
        response.headers = {'content-type': 'text/html; charset=utf-8'}
        response.url = 'https://example.org/opportunity'
        response.text = """
            <html>
              <body>
                <nav>Menu</nav>
                <main>
                  <h1>Consultoria de dados</h1>
                  <p>Termos de referencia com requisitos tecnicos.</p>
                </main>
              </body>
            </html>
        """
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = extract_deep_content('https://example.org/opportunity')

        self.assertEqual(result['status'], 'completed')
        self.assertIn('Consultoria de dados', result['text'])
        self.assertIn('requisitos tecnicos', result['text'])
        self.assertNotIn('Menu', result['text'])

    @patch('apps.scraping.services.deep_extraction._fetch_pdf_text')
    @patch('apps.scraping.services.deep_extraction.requests.get')
    def test_includes_linked_pdf_text(self, mock_get, mock_fetch_pdf_text):
        response = Mock()
        response.headers = {'content-type': 'text/html; charset=utf-8'}
        response.url = 'https://example.org/opportunity'
        response.text = """
            <main>
              <p>Resumo curto da oportunidade.</p>
              <a href="/files/tor.pdf">Download PDF</a>
            </main>
        """
        response.raise_for_status.return_value = None
        mock_get.return_value = response
        mock_fetch_pdf_text.return_value = 'Conteudo completo do TdR em PDF.'

        result = extract_deep_content('https://example.org/opportunity')

        self.assertEqual(result['status'], 'completed')
        self.assertIn('Resumo curto', result['text'])
        self.assertIn('Conteudo completo do TdR em PDF', result['text'])
        mock_fetch_pdf_text.assert_called_once_with('https://example.org/files/tor.pdf', verify_ssl=True)
