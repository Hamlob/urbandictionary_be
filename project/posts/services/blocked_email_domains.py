from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from ..models import BlockedEmailDomain

CACHE_KEY = "blocked_email_domains"

def _normalize_domain(d: str) -> str:
    return (d or "").strip().lower()

def _fetch_from_db():
    domains_qs = BlockedEmailDomain.objects.values_list('domain', flat=True)
    # Normalize once here
    return [ _normalize_domain(d) for d in domains_qs if d ]

def get_blocked_domains():
    """
    Returns a list of normalized blocked domain strings.
    It will use Django cache; on cache miss it fetches from DB and populates cache.
    """
    domains = cache.get(CACHE_KEY)
    if domains is None:
        domains = _fetch_from_db()
        cache.set(CACHE_KEY, domains)
    return domains

def clear_blocked_domains_cache():
    cache.delete(CACHE_KEY)

# Connect signals so any change to BlockedEmailDomain clears the cache immediately.
@receiver(post_save, sender=BlockedEmailDomain)
@receiver(post_delete, sender=BlockedEmailDomain)
def _blocked_domain_changed(sender, instance, **kwargs):
    clear_blocked_domains_cache()
