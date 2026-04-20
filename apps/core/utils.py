from datetime import timedelta
from django.utils import timezone


def get_upcoming_deadlines(days=7):
    """Return a date range for upcoming deadlines."""
    today = timezone.now().date()
    return today, today + timedelta(days=days)
