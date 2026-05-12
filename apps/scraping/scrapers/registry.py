"""
Registry mapping scraper_class names to concrete scraper implementations.
"""
from .base import BaseScraper
from .ugpe_scraper import UGPEScraper
from .ecreee_scraper import ECREEEScraper
from .worldbank_scraper import WorldBankScraper
from .afdb_scraper import AfDBScraper
from .undp_scraper import UNDPScraper
from .luxdev_scraper import LuxDevScraper
from .generic_portal_scraper import GenericPortalScraper
from .fcdo_scraper import FCDOScraper
from .usaid_scraper import USAIDScraper

SCRAPER_REGISTRY = {
    'BaseScraper': BaseScraper,
    'UGPEScraper': UGPEScraper,
    'ECREEEScraper': ECREEEScraper,
    'WorldBankScraper': WorldBankScraper,
    'AfDBScraper': AfDBScraper,
    'UNDPScraper': UNDPScraper,
    'LuxDevScraper': LuxDevScraper,
    'GenericPortalScraper': GenericPortalScraper,
    'FCDOScraper': FCDOScraper,
    'USAIDScraper': USAIDScraper,
}


def get_scraper_class(name: str):
    """Get scraper class by name. Falls back to BaseScraper if not found."""
    return SCRAPER_REGISTRY.get(name, BaseScraper)
