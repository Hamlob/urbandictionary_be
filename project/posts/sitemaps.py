from django.contrib.sitemaps import Sitemap
    
class StaticViewSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5
    protocol = "https"

    def items(self):
        return ['create_post', 'login', 'register', 'account', 'search']

    def location(self, item):
        from django.urls import reverse
        return reverse(item)
    
class DynamicViewSitemap(Sitemap):
    changefreq = "always"
    priority = 0.8
    protocol = "https"

    def items(self):
        return ['feed', 'random_post', 'search']

    def location(self, item):
        from django.urls import reverse
        return reverse(item)
    
sitemaps = {
    'static': StaticViewSitemap,
    'dynamic': DynamicViewSitemap,
}