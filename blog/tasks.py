from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
import time
import logging
import traceback

logger = logging.getLogger('blog')


def send_welcome_email(subscriber_id):
    """
    Send welcome email to new newsletter subscribers.
    
    This function retrieves the subscriber, generates a unique unsubscribe token if needed,
    and sends a personalized welcome email with unsubscribe information.
    
    Args:
        subscriber_id: The ID of the newly created NewsletterSubscriber
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """

    from .models import NewsletterSubscriber
    
    try:
        subscriber = NewsletterSubscriber.objects.get(id=subscriber_id)
        logger.info(f"Preparing welcome email for subscriber: {subscriber.email}")
        
        # Generate unsubscribe token if not exists
        if not subscriber.confirmation_token:
            subscriber.confirmation_token = get_random_string(64)
            subscriber.save()
            logger.debug(f"Generated confirmation token for {subscriber.email}")
        
        # Prepare context for email template
        context = {
            'unsubscribe_url': f"{settings.SITE_URL}{reverse('blog:unsubscribe', args=[subscriber.confirmation_token])}",
            'site_name': settings.SITE_NAME
        }
        
        # Render email templates
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        logger.debug(f"Sending welcome email to {subscriber.email} from {settings.DEFAULT_FROM_EMAIL}")
        
        # Send email
        send_mail(
            subject=f"Welcome to {settings.SITE_NAME}'s Newsletter!",
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscriber.email],
            fail_silently=False,
        )
        
        logger.info(f"✅ Welcome email sent successfully to {subscriber.email}")
        return True

    except NewsletterSubscriber.DoesNotExist:
        logger.error(f"Subscriber with id {subscriber_id} not found")
        return False
    except Exception as e:
        logger.exception(f"❌ Error sending welcome email to subscriber {subscriber_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def send_post_notification_batch(post_id, delay_seconds=0):
    """
    UPDATED: Sends blog post notifications to all active subscribers with comprehensive error handling.
    
    This function implements Gmail-friendly rate limiting by adding delays between
    emails to avoid hitting daily sending limits. It provides detailed progress
    logging and continues sending even if individual emails fail.
    
    Args:
        post_id: The ID of the Post to notify about
        delay_seconds: Seconds to wait between emails (default: 2)
        
    Returns:
        dict: Statistics about the email sending process
    """
    from .models import Post, NewsletterSubscriber
    
    results = {
        'success': True,
        'total_subscribers': 0,
        'emails_sent': 0,
        'emails_failed': 0,
        'failed_emails': [],
        'time_elapsed': 0,
        'error': None
    }
    
    start_time = time.time()
    
    try:
        logger.info(f"Starting send_post_notification_batch for post_id: {post_id}")
        
        # Get the post
        try:
            post = Post.objects.select_related('author').get(id=post_id)
            logger.info(f"Post found: '{post.title}' by {post.author}")
        except Post.DoesNotExist:
            results['success'] = False
            results['error'] = f'Post with id {post_id} not found'
            logger.error(results['error'])
            return results
        
        # Get all active subscribers
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        results['total_subscribers'] = subscribers.count()
        
        if results['total_subscribers'] == 0:
            logger.warning("No active subscribers found")
            results['error'] = 'No active subscribers'
            return results
        
        logger.info(f"Found {results['total_subscribers']} active subscribers")
        
        # Verify email settings
        try:
            logger.debug(f"Email configuration - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}")
            logger.debug(f"From email: {settings.DEFAULT_FROM_EMAIL}")
            logger.debug(f"TLS enabled: {settings.EMAIL_USE_TLS}")
        except AttributeError as e:
            results['success'] = False
            results['error'] = f'Email settings not configured: {e}'
            logger.error(results['error'])
            return results
        
        # Prepare email context (same for all subscribers except unsubscribe_url)
        site_url = settings.SITE_URL.rstrip('/')
        post_url = f"{site_url}{post.get_absolute_url()}"
        
        # Get excerpt (first 200 characters of content, stripped of HTML)
        content_text = strip_tags(post.content)
        excerpt = content_text[:200] + "..." if len(content_text) > 200 else content_text
        
        base_context = {
            'post_title': post.title,
            'post_url': post_url,
            'post_excerpt': excerpt,
            'post_date': post.published_at.strftime('%B %d, %Y') if post.published_at else 'Recently',
            'reading_time': post.reading_time,
            'site_name': settings.SITE_NAME,
        }
        
        # Add featured image if available
        if post.featured_image:
            # If using external storage (like Cloudflare R2), the URL is already complete
            # Otherwise, prepend site_url for local storage
            image_url = post.featured_image.url
            if not image_url.startswith('http'):
                image_url = f"{site_url}{image_url}"
            base_context['post_featured_image'] = image_url
            logger.debug(f"Featured image URL: {base_context['post_featured_image']}")
        
        logger.info("Starting email sending loop...")
        
        # Send emails with rate limiting
        for index, subscriber in enumerate(subscribers, start=1):
            try:
                logger.debug(f"[{index}/{results['total_subscribers']}] Processing {subscriber.email}")
                
                # Add subscriber-specific unsubscribe URL
                context = base_context.copy()
                context['unsubscribe_url'] = f"{site_url}{reverse('blog:unsubscribe', args=[subscriber.confirmation_token])}"
                
                # Render email templates
                html_message = render_to_string('emails/post_notification_email.html', context)
                plain_message = render_to_string('emails/post_notification_email.txt', context)
                
                # Send email
                send_mail(
                    subject=f"New Post: {post.title}",
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=False,
                )
                
                results['emails_sent'] += 1
                logger.info(f"✅ [{results['emails_sent']}/{results['total_subscribers']}] Sent to {subscriber.email}")
                
                # Rate limiting: only sleep if explicitly configured (not on serverless)
                if delay_seconds > 0 and index < results['total_subscribers']:
                    logger.debug(f"Waiting {delay_seconds}s before next email...")
                    time.sleep(delay_seconds)
                
            except Exception as email_error:
                results['emails_failed'] += 1
                results['failed_emails'].append(subscriber.email)
                logger.error(f"❌ Failed to send to {subscriber.email}: {str(email_error)}")
                logger.error(f"Error details: {traceback.format_exc()}")
                # Continue with next subscriber even if this one failed
                continue
        
        results['time_elapsed'] = round(time.time() - start_time, 2)
        
        logger.info(
            f"📊 Email batch complete - "
            f"Sent: {results['emails_sent']}, "
            f"Failed: {results['emails_failed']}, "
            f"Time: {results['time_elapsed']}s"
        )
        
        return results
        
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
        results['time_elapsed'] = round(time.time() - start_time, 2)
        logger.exception(f"❌ Critical error in send_post_notification_batch: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return results


# Keep old function name for backwards compatibility
def send_post_notification(post_id):
    """Wrapper for backwards compatibility"""
    logger.info(f"send_post_notification called (wrapper) for post_id: {post_id}")
    return send_post_notification_batch(post_id)