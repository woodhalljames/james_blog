from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post
from django.utils import timezone

class PostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9
    protocol = 'https'

    def items(self):
        return Post.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).order_by('-published_at')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.5
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return ['blog:post_list', 'blog:business']
    
    def location(self, item):
        return reverse(item)