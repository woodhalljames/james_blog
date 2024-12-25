from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.utils.crypto import get_random_string



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
        
        # Generate unsubscribe token if not exists
        if not subscriber.confirmation_token:
            subscriber.confirmation_token = get_random_string(64)
            subscriber.save()
        
        # Prepare context for email template
        context = {
            'unsubscribe_url': f"{settings.SITE_URL}{reverse('blog:unsubscribe', args=[subscriber.confirmation_token])}",
            'site_name': settings.SITE_NAME
        }
        
        # Render email templates
        html_message = render_to_string('emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=f"Welcome to {settings.SITE_NAME}'s Newsletter!",
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscriber.email],
            fail_silently=False,
        )
        
        return True

    except Exception as e:
        # Log the error - replace with proper logging in production
        print(f"Error sending welcome email: {e}")
        return False



def send_post_notification(post_id):
    """
    Sends blog post notifications to all active subscribers.
    Handles failures silently to ensure maximum delivery.
    
    This function follows a "best effort" approach - if an individual email fails,
    it continues with the remaining subscribers. This ensures that one failed
    delivery doesn't prevent other subscribers from receiving their notifications.
    """
    from .models import Post, NewsletterSubscriber
    
    try:
        # Get the post details first - if this fails, we shouldn't try sending any emails
        post = Post.objects.get(id=post_id)
        print(f"Found post: {post.title}")  # Keep this logging for basic monitoring
        
        # Get all active subscribers in one query
        active_subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        print(f"Found {active_subscribers.count()} subscribers")
        
        # Track successful sends
        successful_sends = 0
        
        # Process each subscriber - using a simple loop for clarity
        for subscriber in active_subscribers:
            try:
                # Create email content for this subscriber
                context = {
                    'post_title': post.title,
                    'post_url': f"{settings.SITE_URL}{post.get_absolute_url()}",
                    'post_content': post.content,  # Full content - template will handle truncation
                    'site_name': settings.SITE_NAME,
                    'unsubscribe_url': f"{settings.SITE_URL}{reverse('blog:unsubscribe', args=[subscriber.confirmation_token])}"
                }
                
                # Render and send the email
                html_message = render_to_string('emails/new_post_notification.html', context)
                send_mail(
                    subject=f"New Post: {post.title}",
                    message=strip_tags(html_message),
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=True  # Key setting for silent failure handling
                )
                successful_sends += 1
                
            except:  # Catch any errors but continue with next subscriber
                continue
        
        # Return a simple success indication
        return {'success': True, 'sent': successful_sends}
        
    except Exception as e:
        print(f"Critical error in send_post_notification: {e}")  # Keep critical error logging
        return {'success': False, 'message': str(e)}