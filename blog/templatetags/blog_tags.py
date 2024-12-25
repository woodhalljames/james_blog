from django import template
from django.db.models import Count
from ..models import Post, NewsletterSubscriber

register = template.Library()

@register.simple_tag
def total_subscribers():
    """Return the total number of active subscribers"""
    return NewsletterSubscriber.objects.filter(is_active=True).count()

@register.simple_tag
def total_posts():
    """Return the total number of published posts"""
    return Post.objects.filter(is_published=True).count()

@register.simple_tag
def get_recent_posts(count=5):
    """Return the specified number of recent published posts"""
    return Post.objects.filter(is_published=True).order_by('-published_at')[:count]

@register.simple_tag
def get_popular_posts(count=5):
    """Return the specified number of most viewed posts"""
    return Post.objects.filter(is_published=True).order_by('-view_count')[:count]