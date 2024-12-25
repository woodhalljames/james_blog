from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import F
from django.utils import timezone
from .models import Post, NewsletterSubscriber
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import json
from django.utils.crypto import get_random_string  # Add this import
from django.contrib import messages 
from django.views.generic import TemplateView
from .tasks import send_welcome_email, send_post_notification
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from taggit.models import Tag


class PublishedPostMixin:
    """Mixin to handle published posts logic"""
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Staff can see all posts
        if self.request.user.is_staff:
            return queryset
        
        return queryset.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('author')
    

#@method_decorator(cache_page(60 * 60 * 24), name='dispatch')    
class PostListView(PublishedPostMixin, ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            return Post.objects.filter(tags__in=[tag])
        return Post.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('author').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs.get('tag_slug'):
            context['tag'] = get_object_or_404(Tag, slug=self.kwargs['tag_slug'])
        return context

    
class PostDetailView(PublishedPostMixin, DetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'author'
        ).prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()

        session_key = f'liked_post_{post.id}'
        context['liked'] = self.request.session.get(session_key, False)
        
        context['schema_markup'] = post.get_full_schema_markup()

        context['meta'] = {
            'title': f"{post.title} | James",
            'description': post.meta_description,
            'type': 'article',
            'image': post.featured_image.url if post.featured_image else None,
        }
        
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count
        self.object.increment_views()
        return response
    
@staff_member_required
def publish_post(request, post_id):
    """
    View to handle post publication and trigger notifications.
    Ensures proper error handling and notification sending.
    """
    post = get_object_or_404(Post, id=post_id)
    
    try:
        # Set publication fields
        if not post.published_at:
            post.published_at = timezone.now()
        post.is_published = True
        post.save()
        
        # Send notifications
        notification_result = send_post_notification(post.id)
        
        if not notification_result.get('success'):
            messages.warning(
                request,
                f"Post published but there was an error sending notifications: {notification_result.get('message')}"
            )
        else:
            messages.success(
                request,
                f"Post published successfully. Sent to {notification_result.get('sent')} subscribers."
            )
            
    except Exception as e:
        messages.error(request, f"Error publishing post: {str(e)}")
        
    return redirect('blog:post_detail', slug=post.slug)

@require_http_methods(["POST"])
def like_post(request, post_id):
    #use cache to get current like
    cache_key = f'post_likes_{post_id}'
    likes_count = cache.get(cache_key)

    #if not in cache, fetch
    if likes_count is None: 
        post = get_object_or_404(Post, id=post_id)
        likes_count = post.like_count
        cache.set(cache_key, likes_count, timeout=3600) #cache for an hour
    
    session_key = f'liked_post_{post_id}'

    if not request.session.get(session_key, False):
        try:
            #atomic update of likes_count
            Post.objects.filter(id=post_id).update(like_count=F('like_count') + 1)
            #update cache
            likes_count = cache.incr(cache_key)
            #update session
            request.session[session_key] = True
            return JsonResponse({'likes_count': likes_count})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'likes_count': likes_count})

@require_http_methods(["POST"])
@ensure_csrf_cookie
def subscribe_newsletter(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Email is required'
            }, status=400)
            
        if NewsletterSubscriber.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Already subscribed!'}, status=400)
            
        subscriber = NewsletterSubscriber.objects.create(
            email=email,
            confirmation_token=get_random_string(64)
        )
        send_welcome_email(subscriber.id)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thank you for subscribing!'
        })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["GET", "POST"])
def unsubscribe_newsletter(request, token):
    subscriber = get_object_or_404(NewsletterSubscriber, 
                                 confirmation_token=token,
                                 is_active=True)
    
    if request.method == "POST":
        subscriber.is_active = False
        subscriber.save()
        return render(request, 'email/unsubscribe_success.html')
        
    return render(request, 'email/unsubscribe_confirm.html', {'subscriber': subscriber})



class BusinessView(TemplateView):
    template_name = 'business.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data you need for the business page
        context['professional_title'] = "Project Manager"
        context['business_profile'] = {
            'name': 'James Woodhall',
            'title': 'Project Manager',
            'email': 'woodhalljames@gmail.com',  # Update with your business email
              # Update with your LinkedIn
            'github': 'https://github.com/woodhalljames'  # Update with your GitHub
        }
        return context


def error_404(request, exception):
    context = {'error_code': '404',
               'error_message': 'Page Not Found',
              }
    return render(request, 'error.html', context, status=404)

def error_500(request):
    context = {'error_code': '500',
               'error_message': 'Server Error',
               }
    return render(request, 'error.html', context, status=500)

def error_403(request, exception):
    context = {'error_code': '403',
               'error_message': 'Access Denied',
              }
    return render(request, 'error.html', context, status=403)

def error_400(request, exception):
    context = {'error_code': '400',
               'error_message': 'Bad Request',
               }
    return render(request, 'error.html', context, status=400)