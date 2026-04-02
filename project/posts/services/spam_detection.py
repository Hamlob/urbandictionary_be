from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import re

from ..models import SpamRegEx

CACHE_KEY = "spam_regex_patterns"

def _fetch_from_db():
    return SpamRegEx.objects.values_list('pattern', flat=True)

def get_spam_patterns():
    """
    Returns a list of normalized spam regex patterns.
    It will use Django cache; on cache miss it fetches from DB and populates cache.
    """
    patterns = cache.get(CACHE_KEY)
    if patterns is None:
        patterns = _fetch_from_db()
        patterns = [re.compile(rf'{pattern}', re.IGNORECASE) for pattern in patterns]
        cache.set(CACHE_KEY, patterns)
    return patterns

def clear_spam_patterns_cache():
    cache.delete(CACHE_KEY)

# Connect signals so any change to SpamRegEx clears the cache immediately.
@receiver(post_save, sender=SpamRegEx)
@receiver(post_delete, sender=SpamRegEx)
def _spam_pattern_changed(sender, instance, **kwargs):
    clear_spam_patterns_cache()


def is_spam_text(title: str, text: str, example: str) -> bool:
    """Check if any of the given text fields match spam patterns defined in the database.

    Returns:
        bool: True if any of the fields match a spam pattern, False otherwise.
    """
    spam_patterns = get_spam_patterns()
    for pattern in spam_patterns:
        if pattern.search(title) or pattern.search(text) or pattern.search(example):
            return True
    return False