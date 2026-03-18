from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django_summernote.admin import SummernoteModelAdmin
from .models import Author, Post, PostRevision, NewsletterSubscriber, BusinessProfile
from .tasks import send_post_notification_batch
import logging

logger = logging.getLogger('blog')


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

    # Specify which fields should use Summernote editor
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
        }),
        ('Email Notifications', {
            'fields': ('send_notification_button',),
        }),
    )
    readonly_fields = ('view_count', 'like_count', 'thumbnail', 'send_notification_button')

    def send_notification_button(self, obj):
        if not obj.pk:
            return "Save the post first."
        url = reverse('admin:blog_post_send_notifications', args=[obj.pk])
        label = "Resend Notifications" if obj.is_published else "Send Notifications (publish first)"
        return format_html('<a class="button" href="{}">📧 {}</a>', url, label)
    send_notification_button.short_description = 'Newsletter'

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
        UPDATED: Admin action to send email notifications with comprehensive error handling.
        """
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one post at a time to send notifications.",
                level=messages.WARNING
            )
            return
        
        post = queryset.first()
        
        # Log the attempt
        logger.info(f"Admin action triggered: Sending notifications for post '{post.title}' (ID: {post.id})")
        
        if not post.is_published:
            self.message_user(
                request,
                f"Post '{post.title}' is not published. Please publish it first.",
                level=messages.WARNING
            )
            logger.warning(f"Attempt to send notifications for unpublished post: {post.id}")
            return
        
        # Check if there are any subscribers
        from .models import NewsletterSubscriber
        active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
        
        if active_subscribers == 0:
            self.message_user(
                request,
                "No active subscribers found. Cannot send notifications.",
                level=messages.WARNING
            )
            logger.warning("No active subscribers in database")
            return
        
        # Show progress message
        self.message_user(
            request,
            f"Sending email notifications for '{post.title}' to {active_subscribers} subscribers. This may take a few minutes...",
            level=messages.INFO
        )
        logger.info(f"Starting to send {active_subscribers} emails...")
        
        try:
            # Send notifications with error handling
            results = send_post_notification_batch(post.id)
            
            # Log the results
            logger.info(f"Email batch complete: {results}")
            
            if results['success']:
                message = (
                    f"✅ Email notifications sent successfully! "
                    f"Sent: {results['emails_sent']}, "
                    f"Failed: {results['emails_failed']}, "
                    f"Time: {results['time_elapsed']}s"
                )
                
                if results['emails_failed'] > 0:
                    failed_list = ', '.join(results['failed_emails'][:5])
                    message += f" | Failed emails: {failed_list}"
                    if len(results['failed_emails']) > 5:
                        message += f" and {len(results['failed_emails']) - 5} more"
                    logger.error(f"Failed emails: {results['failed_emails']}")
                
                level = messages.SUCCESS if results['emails_failed'] == 0 else messages.WARNING
                self.message_user(request, message, level=level)
            else:
                error_msg = results.get('error', 'Unknown error')
                self.message_user(
                    request,
                    f"❌ Error sending notifications: {error_msg}",
                    level=messages.ERROR
                )
                logger.error(f"Email batch failed: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            self.message_user(
                request,
                f"❌ Critical error sending notifications: {error_msg}",
                level=messages.ERROR
            )
            logger.exception(f"Exception in send_email_notifications: {e}")
    
    send_email_notifications.short_description = "📧 Send email notifications to subscribers"

    actions = ['make_published', 'make_draft', 'send_email_notifications']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:post_id>/send-notifications/',
                self.admin_site.admin_view(self.send_notifications_view),
                name='blog_post_send_notifications',
            ),
        ]
        return custom + urls

    def send_notifications_view(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        change_url = reverse('admin:blog_post_change', args=[post_id])

        if not post.is_published:
            self.message_user(
                request,
                f"'{post.title}' is not published. Publish it first.",
                level=messages.WARNING,
            )
            return redirect(change_url)

        active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
        if active_subscribers == 0:
            self.message_user(request, "No active subscribers found.", level=messages.WARNING)
            return redirect(change_url)

        logger.info(f"Sending notifications for post '{post.title}' (ID: {post_id}) to {active_subscribers} subscribers")
        results = send_post_notification_batch(post_id)

        if results['success']:
            msg = (
                f"Sent: {results['emails_sent']}, "
                f"Failed: {results['emails_failed']}, "
                f"Time: {results['time_elapsed']}s"
            )
            if results['emails_failed']:
                msg += f" | Failed: {', '.join(results['failed_emails'][:5])}"
            level = messages.SUCCESS if results['emails_failed'] == 0 else messages.WARNING
        else:
            msg = f"Error: {results.get('error', 'Unknown error')}"
            level = messages.ERROR

        self.message_user(request, msg, level=level)
        return redirect(change_url)

    def save_model(self, request, obj, form, change):
        """Override to add logging"""
        if change:
            logger.info(f"Post updated: {obj.title} (ID: {obj.id})")
        else:
            logger.info(f"New post created: {obj.title}")
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
    actions = ['activate_subscribers', 'deactivate_subscribers', 'test_email']

    def activate_subscribers(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} subscribers")
    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} subscribers")
    deactivate_subscribers.short_description = "Deactivate selected subscribers"
    
    def test_email(self, request, queryset):
        """Send a test email to verify email configuration"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one subscriber to test email",
                level=messages.WARNING
            )
            return
        
        subscriber = queryset.first()
        
        try:
            send_mail(
                subject="Test Email from James' Blog",
                message="This is a test email. If you received this, your email configuration is working!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=False,
            )
            self.message_user(
                request,
                f"✅ Test email sent successfully to {subscriber.email}",
                level=messages.SUCCESS
            )
            logger.info(f"Test email sent to {subscriber.email}")
        except Exception as e:
            self.message_user(
                request,
                f"❌ Failed to send test email: {str(e)}",
                level=messages.ERROR
            )
            logger.exception(f"Test email failed: {e}")
    
    test_email.short_description = "📧 Send test email"


@admin.register(BusinessProfile)
class BusinessProfileAdmin(SummernoteModelAdmin):
    """
    Simplified admin for business profile with Summernote editor.
    """
    summernote_fields = ('content',)
    
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
    
    def has_add_permission(self, request):
        return not BusinessProfile.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False