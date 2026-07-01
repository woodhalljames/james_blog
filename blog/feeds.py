from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from .models import Post


class LatestPostsFeed(Feed):
    title = "James' Blog"
    description = "Writing about things that make life enjoyable."

    def link(self):
        return reverse('blog:post_list')

    def items(self):
        return Post.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).order_by('-published_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.meta_description or ''

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_author_name(self, item):
        return 'James Woodhall'
