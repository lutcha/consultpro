import logging
from io import BytesIO
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 25
MAX_TEXT_LENGTH = 50000
MAX_PDF_LINKS = 2

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 '
        'ConsultProBot/1.0 (+https://consultpro.cv/bot)'
    ),
    'Accept': 'text/html,application/pdf,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
}


def extract_deep_content(url: str, base_url: str = '') -> dict:
    """
    Fetch an opportunity detail URL and extract readable page/PDF text.

    The extractor is deliberately defensive: callers can keep the scraping
    pipeline alive even when a target site blocks, times out, or returns
    content that cannot be parsed.
    """
    if not url:
        return {'status': 'skipped', 'text': '', 'url': '', 'error': 'missing_url'}

    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'}:
        return {'status': 'skipped', 'text': '', 'url': url, 'error': 'unsupported_url_scheme'}

    try:
        response = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning('Deep extraction fetch failed for %s: %s', url, exc)
        return {'status': 'failed', 'text': '', 'url': url, 'error': str(exc)[:300]}

    content_type = response.headers.get('content-type', '').lower()
    final_url = response.url or url

    try:
        if 'pdf' in content_type or final_url.lower().endswith('.pdf'):
            text = _extract_pdf_text(response.content)
            return _result('completed' if text else 'empty', text, final_url)

        html_text, pdf_links = _extract_html_text_and_pdf_links(response.text, final_url, base_url)
        pdf_text_parts = []
        for pdf_url in pdf_links[:MAX_PDF_LINKS]:
            pdf_text = _fetch_pdf_text(pdf_url)
            if pdf_text:
                pdf_text_parts.append(f"PDF: {pdf_url}\n{pdf_text}")

        combined = '\n\n'.join(part for part in [html_text, *pdf_text_parts] if part).strip()
        return _result('completed' if combined else 'empty', combined, final_url)
    except Exception as exc:
        logger.warning('Deep extraction parse failed for %s: %s', final_url, exc, exc_info=True)
        return {'status': 'failed', 'text': '', 'url': final_url, 'error': str(exc)[:300]}


def _result(status: str, text: str, url: str) -> dict:
    text = (text or '').strip()
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + '\n\n[Conteudo truncado para extracao IA]'
    return {
        'status': status,
        'text': text,
        'url': url,
        'length': len(text),
    }


def _extract_html_text_and_pdf_links(html: str, final_url: str, base_url: str = '') -> tuple[str, list[str]]:
    soup = BeautifulSoup(html or '', 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer']):
        tag.decompose()

    root = (
        soup.find('main')
        or soup.find('article')
        or soup.find(attrs={'role': 'main'})
        or soup.body
        or soup
    )
    text = root.get_text('\n', strip=True)
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 2]
    clean_text = '\n'.join(lines)

    pdf_links = []
    for link in soup.find_all('a', href=True):
        href = link['href'].strip()
        label = link.get_text(' ', strip=True).lower()
        if '.pdf' not in href.lower() and 'pdf' not in label and 'download' not in label:
            continue
        absolute = urljoin(final_url or base_url, href)
        if absolute not in pdf_links:
            pdf_links.append(absolute)

    return clean_text, pdf_links


def _fetch_pdf_text(url: str) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        return _extract_pdf_text(response.content)
    except Exception as exc:
        logger.warning('Linked PDF extraction failed for %s: %s', url, exc)
        return ''


def _extract_pdf_text(content: bytes) -> str:
    if not content:
        return ''
    from PyPDF2 import PdfReader

    reader = PdfReader(BytesIO(content))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or '')
        except Exception as exc:
            logger.warning('PDF page extraction failed: %s', exc)
    return '\n'.join(parts).strip()
