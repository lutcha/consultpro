"""
Proxy session helper for scraping sources that explicitly opt in.
"""
import logging
import os
import threading
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_proxy_index = 0
_proxy_cache_raw = None
_proxy_cache = []


def _load_proxies():
    global _proxy_cache_raw, _proxy_cache

    raw_value = os.environ.get('SCRAPING_PROXIES', '')
    if raw_value == _proxy_cache_raw:
        return _proxy_cache

    proxies = []
    for value in [item.strip() for item in raw_value.split(',') if item.strip()]:
        parsed = urlparse(value)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            logger.warning("Invalid proxy URL skipped: %s", value)
            continue
        proxies.append(value)

    _proxy_cache_raw = raw_value
    _proxy_cache = proxies
    return proxies


def get_proxy_session(verify_ssl=True) -> requests.Session:
    """
    Return a requests session with the next configured proxy, if any.

    # Uso: chamar get_proxy_session() EM VEZ de criar uma sessao simples
    # quando fontes de scraping tiverem scraper_config['use_proxy'] = True.
    # A camada de tasks ou subclasses fazem opt-in; base.py nao e modificado.
    """
    global _proxy_index

    session = requests.Session()
    session.verify = verify_ssl

    with _lock:
        proxies = _load_proxies()
        if not proxies:
            return session

        proxy_url = proxies[_proxy_index % len(proxies)]
        _proxy_index += 1

    session.proxies.update({
        'http': proxy_url,
        'https': proxy_url,
    })
    return session
