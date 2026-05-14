"""
Helpers for classifying scraping sources in admin and API serializers.
"""


def get_source_category(source) -> str:
    """Devolve a categoria funcional da fonte para organizacao do catalogo."""
    configured = (
        (source.scraper_config or {}).get('source_category')
        or (source.filters or {}).get('category')
    )
    if configured:
        return configured

    haystack = f"{source.name} {source.organization} {source.url}".lower()

    if source.source_type == 'rss':
        return 'aggregator'
    if source.source_type == 'api':
        return 'grants'
    if any(token in haystack for token in ('ugpe', 'cabo verde', 'cv ', '.cv')):
        return 'national'
    if any(token in haystack for token in ('european commission', 'eu ', 'funding', 'grant', 'undp')):
        return 'grants'
    if any(token in haystack for token in ('giz', 'luxdev', 'fcdo', 'usaid')):
        return 'bilateral'
    if any(token in haystack for token in ('world bank', 'afdb', 'african development bank', 'ecreee', 'ecowas', 'united nations')):
        return 'multilateral'
    if source.scraper_class == 'GenericPortalScraper':
        return 'aggregator'
    return 'multilateral'


def get_scraper_kind(source) -> str:
    """Identifica se a fonte usa scraper dedicado, generico, API, RSS ou esta pausada."""
    if source.status == 'paused':
        return 'paused'
    if source.source_type in ('api', 'rss'):
        return source.source_type
    if source.scraper_class == 'GenericPortalScraper':
        return 'generic'
    return 'dedicated'
