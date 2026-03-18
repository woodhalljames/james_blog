from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
# SummernoteTextField removed - using regular TextField now to prevent sanitization
from django_summernote.models import AbstractAttachment
from taggit.managers import TaggableManager
from PIL import Image
from io import BytesIO
import os
import json
from django.utils.html import strip_tags
from django.core.files import File
from django.conf import settings
from django.core.files.storage import default_storage


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Professional bio"
    )
    profile_image = models.ImageField(
        upload_to='authors/',
        blank=True
    )

    def full_name(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    def __str__(self):
        return self.full_name() or self.user.username


class Post(models.Model):
    # Basic Fields
    title = models.CharField(
        max_length=200,
        help_text="The title of your blog post"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly version of the title"
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name='posts'
    )
    # CHANGED: Using TextField instead of SummernoteTextField to prevent sanitization
    # The admin still uses Summernote editor, but the field doesn't apply sanitization
    content = models.TextField(
        help_text="Blog post content with rich text formatting and images"
    )

    # SEO Fields
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Maximum 160 characters for SEO. If left blank, first 160 characters of content will be used."
    )
    meta_keywords = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated keywords for SEO"
    )

    # Image Fields
    featured_image = models.ImageField(
        upload_to='blog/%Y/%m/',
        blank=True,
        help_text="Main image for the blog post"
    )
    featured_image_alt = models.CharField(
        max_length=100,
        blank=True,
        help_text="Alt text for featured image"
    )

    # Publishing Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this post should go live"
    )
    last_modified = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(
        default=False,
        help_text="Set to true to make this post public"
    )
    view_count = models.PositiveIntegerField(default=0)

    # Categorization Fields
    tags = TaggableManager(
        blank=True,
        help_text="Add relevant tags to help readers find related content"
    )

    # Additional Fields
    reading_time = models.PositiveIntegerField(
        default=5,
        help_text="Estimated reading time in minutes"
    )
    thumbnail = models.ImageField(
        upload_to='blog/thumbnails/%Y/%m/',
        blank=True,
        help_text="Automatically generated thumbnail"
    )

    like_count = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        indexes = [
            models.Index(fields=['-published_at', '-created_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Returns the canonical URL for this post"""
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def create_thumbnail(self, size=(280, 200)):
        """Creates a thumbnail of the featured image"""
        if not self.featured_image:
            return

        image = Image.open(self.featured_image)

        if image.mode == 'RGBA':
            image = image.convert('RGB')

        image.thumbnail(size, Image.Resampling.LANCZOS)

        thumb_io = BytesIO()
        image.save(thumb_io, 'JPEG', quality=85)

        thumbnail_name = f'thumb_{os.path.basename(self.featured_image.name)}'

        self.thumbnail.save(
            thumbnail_name,
            File(thumb_io),
            save=False
        )

    def increment_views(self):
        """Increment the view count in a thread-safe manner"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])

    def is_scheduled(self):
        """Check if post is scheduled for future publication"""
        return self.is_published and self.published_at and self.published_at > timezone.now()

    def get_related_posts(self):
        """Get posts with similar tags, limited to 3 results"""
        post_tags_ids = self.tags.values_list('id', flat=True)
        related_posts = Post.objects.filter(
            tags__in=post_tags_ids,
            is_published=True,
            published_at__lte=timezone.now()
        ).exclude(id=self.id)
        return related_posts.distinct()[:3]

    def get_thumbnail_url(self):
        """Returns the thumbnail URL or featured image URL as fallback"""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.featured_image:
            return self.featured_image.url
        return None

    def generate_schema_markup(self):
        """
        Generates Schema.org Article markup in JSON-LD format for the blog post.
        This helps search engines better understand the content structure.
        """
        try:
            site_url = settings.SITE_URL.rstrip('/')
            article_url = f"{site_url}{self.get_absolute_url()}"

            schema = {
                "@context": "https://schema.org",
                "@type": "BlogPosting",
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": article_url
                },
                "headline": self.title,
                "description": self.meta_description,
                "image": [
                    f"{site_url}{self.featured_image.url}" if self.featured_image else None
                ],
                "author": {
                    "@type": "Person",
                    "name": self.author.full_name(),
                    "url": settings.SITE_URL,
                },
                "publisher": {
                    "@type": "Organization",
                    "name": settings.SITE_NAME,
                    "logo": {
                        "@type": "ImageObject",
                        "url": f"{site_url}{settings.SITE_LOGO}"
                    }
                },
                "datePublished": self.published_at.isoformat() if self.published_at else None,
                "dateModified": self.updated_at.isoformat(),
                "keywords": self.meta_keywords,
                "articleBody": strip_tags(self.content),
                "wordCount": len(strip_tags(self.content).split()),
            }

            schema = {k: v for k, v in schema.items() if v is not None}
            return json.dumps(schema, ensure_ascii=False)

        except AttributeError:
            print("Warning: SITE_URL not properly configured in settings")
            return "{}"

    def generate_breadcrumb_schema(self):
        """
        Generates Schema.org BreadcrumbList markup in JSON-LD format.
        This helps search engines understand the site's hierarchy.
        """
        try:
            site_url = settings.SITE_URL.rstrip('/')

            schema = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": site_url
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Blog",
                        "item": f"{site_url}/blog/"
                    }
                ]
            }

            schema["itemListElement"].append({
                "@type": "ListItem",
                "position": len(schema["itemListElement"]) + 1,
                "name": self.title,
                "item": f"{site_url}{self.get_absolute_url()}"
            })

            return json.dumps(schema, ensure_ascii=False)
        except AttributeError:
            print("Warning: SITE_URL not properly configured in settings")
            return "{}"

    def get_full_schema_markup(self):
        """
        Returns a combined schema markup for the page including both
        the article and breadcrumb schemas.
        """
        return f"""
        <script type="application/ld+json">
        {self.generate_schema_markup()}
        </script>
        <script type="application/ld+json">
        {self.generate_breadcrumb_schema()}
        </script>
        """

    def save(self, *args, **kwargs):
        """
        Override the save method to handle automatic field population
        and thumbnail generation.
        """
        if not self.slug:
            self.slug = slugify(self.title)

        if self.is_published and not self.published_at:
            self.published_at = timezone.now()

        if not self.meta_description and self.content:
            stripped_content = strip_tags(self.content)
            self.meta_description = (stripped_content[:157] + "..."
                                   if len(stripped_content) > 160
                                   else stripped_content)

        if not self.id or (self.featured_image and not self.thumbnail):
            self.create_thumbnail()

        super().save(*args, **kwargs)


class PostRevision(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='revisions'
    )
    content = models.TextField()
    revision_date = models.DateTimeField(auto_now_add=True)
    editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    revision_note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Note describing the changes made in this revision"
    )

    class Meta:
        ordering = ['-revision_date']
        verbose_name = 'Post Revision'
        verbose_name_plural = 'Post Revisions'

    def __str__(self):
        return f"Revision of {self.post.title} - {self.revision_date}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    confirmation_token = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'session_key']


class SummernoteAttachment(AbstractAttachment):
    """
    UPDATED: Model to store Summernote attachments/images with proper storage handling
    
    This model now uses the default storage backend configured in settings.STORAGES
    instead of trying to instantiate storage directly in migrations.
    """
    
    # Override the file field to use default storage properly
    file = models.FileField(
        upload_to='summernote/%Y/%m/%d/',
        storage=default_storage,  # Use the default storage from settings
    )
    
    def __str__(self):
        return self.name if self.name else str(self.file.name)

    class Meta:
        verbose_name = 'Summernote Attachment'
        verbose_name_plural = 'Summernote Attachments'


# Business Profile Model

class BusinessProfile(models.Model):
    """
    Model for business/professional profile information.
    """
    name = models.CharField(
        max_length=200, 
        default="James Woodhall",
        help_text="Your full name"
    )
    title = models.CharField(
        max_length=200, 
        default="Web Developer & Digital Marketer",
        help_text="Your professional title"
    )
    email = models.EmailField(
        default="woodhalljames@gmail.com",
        help_text="Contact email"
    )
    summary = models.TextField(
        blank=True,
        default='',
        help_text="Brief professional summary (optional)"
    )

    phone = models.CharField(
        max_length=50, 
        default="+1 724-759-4858",
        help_text="Contact phone number"
    )
    github = models.URLField(
        blank=True, 
        default="https://github.com/woodhalljames",
        help_text="GitHub profile URL"
    )
    linkedin = models.URLField(
        blank=True,
        help_text="LinkedIn profile URL"
    )
    
    professional_image = models.ImageField(
        upload_to='business/',
        blank=True,
        help_text="Professional headshot photo"
    )
    
    resume_pdf = models.FileField(
        upload_to='business/resumes/',
        blank=True,
        help_text="Upload your resume/CV PDF for download"
    )
    
    # CHANGED: Using TextField instead of SummernoteTextField to prevent sanitization
    content = models.TextField(
        help_text="Your professional profile content - add your summary, experience, projects, education, etc.",
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Business Profile'
        verbose_name_plural = 'Business Profile'
    
    def __str__(self):
        return f"{self.name} - {self.title}"
    
    @classmethod
    def get_profile(cls):
        """Get or create the profile instance"""
        profile, created = cls.objects.get_or_create(pk=1)
        return profile