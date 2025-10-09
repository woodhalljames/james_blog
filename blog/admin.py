from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django_summernote.admin import SummernoteModelAdmin
from .models import Author, Post, PostRevision, NewsletterSubscriber, BusinessProfile
from .tasks import send_post_notification_batch


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'show_profile_image')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)

    def show_profile_image(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                             obj.profile_image.url)
        return "No image"
    show_profile_image.short_description = 'Profile Image'


@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):
    list_display = ['title', 'author', 'is_published', 'published_at',
                   'view_count', 'like_count']
    list_filter = ['is_published', 'created_at', 'published_at', 'author']
    search_fields = ['title', 'content', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'published_at'
    
    # Summernote fields
    summernote_fields = ('content',)
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'content')
        }),
        ('Images', {
            'fields': ('featured_image', 'featured_image_alt', 'thumbnail')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'reading_time', 'tags')
        }),
        ('Statistics', {
            'fields': ('view_count', 'like_count'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('view_count', 'like_count', 'thumbnail')

    def show_thumbnail(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" />',
                             obj.thumbnail.url)
        return "No thumbnail"
    show_thumbnail.short_description = 'Thumbnail'

    def make_published(self, request, queryset):
        queryset.update(is_published=True)
    make_published.short_description = "Mark selected posts as published"

    def make_draft(self, request, queryset):
        queryset.update(is_published=False)
    make_draft.short_description = "Mark selected posts as draft"
    
    def send_email_notifications(self, request, queryset):
        """
        Admin action to send email notifications for selected posts.
        Includes rate limiting and detailed progress feedback.
        """
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one post at a time to send notifications.",
                level=messages.WARNING
            )
            return
        
        post = queryset.first()
        
        if not post.is_published:
            self.message_user(
                request,
                f"Post '{post.title}' is not published. Please publish it first.",
                level=messages.WARNING
            )
            return
        
        # Send notifications with rate limiting
        self.message_user(
            request,
            f"Sending email notifications for '{post.title}'. This may take a few minutes...",
            level=messages.INFO
        )
        
        results = send_post_notification_batch(post.id)
        
        if results['success']:
            message = (
                f"Email notifications sent successfully! "
                f"Sent: {results['emails_sent']}, "
                f"Failed: {results['emails_failed']}, "
                f"Time: {results['time_elapsed']}s"
            )
            
            if results['emails_failed'] > 0:
                message += f" | Failed emails: {', '.join(results['failed_emails'][:5])}"
                if len(results['failed_emails']) > 5:
                    message += f" and {len(results['failed_emails']) - 5} more"
            
            level = messages.SUCCESS if results['emails_failed'] == 0 else messages.WARNING
            self.message_user(request, message, level=level)
        else:
            self.message_user(
                request,
                f"Error sending notifications: {results.get('error', 'Unknown error')}",
                level=messages.ERROR
            )
    
    send_email_notifications.short_description = "📧 Send email notifications to subscribers"

    actions = ['make_published', 'make_draft', 'send_email_notifications']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(PostRevision)
class PostRevisionAdmin(admin.ModelAdmin):
    list_display = ('post', 'editor', 'revision_date', 'revision_note')
    list_filter = ('revision_date', 'editor')
    search_fields = ('post__title', 'revision_note', 'content')
    raw_id_fields = ('post', 'editor')
    readonly_fields = ('revision_date',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at', 'confirmation_token')
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        queryset.update(is_active=True)
    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_subscribers.short_description = "Deactivate selected subscribers"


# Replace the BusinessProfileAdmin section in your admin.py with this:

@admin.register(BusinessProfile)
class BusinessProfileAdmin(SummernoteModelAdmin):
    """
    Simplified admin for business profile with Summernote editor.
    """
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'professional_image')
        }),
        ('Professional Summary', {
            'fields': ('summary',),
            'description': 'Brief professional summary or tagline'
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'github', 'linkedin')
        }),
        ('Resume/CV', {
            'fields': ('resume_pdf',),
        }),
        ('Profile Content', {
            'fields': ('content',),
        }),
    )
    
    summernote_fields = ('content',)
    
    def has_add_permission(self, request):
        return not BusinessProfile.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False