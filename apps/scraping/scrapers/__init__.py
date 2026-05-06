from .base import BaseScraper
from .registry import SCRAPER_REGISTRY, get_scraper_class
from .ugpe_scraper import UGPEScraper
from .ecreee_scraper import ECREEEScraper
from .worldbank_scraper import WorldBankScraper
from .afdb_scraper import AfDBScraper
from .undp_scraper import UNDPScraper
from .generic_portal_scraper import GenericPortalScraper

__all__ = [
    'BaseScraper',
    'SCRAPER_REGISTRY',
    'get_scraper_class',
    'UGPEScraper',
    'ECREEEScraper',
    'WorldBankScraper',
    'AfDBScraper',
    'UNDPScraper',
    'GenericPortalScraper',
]
