from django.urls import path, include
from . import views




app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('tag/<slug:tag_slug>/', views.PostListView.as_view(), name='post_list_by_tag'),
    path('blog/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe'),
    path('unsubscribe/<str:token>/', views.unsubscribe_newsletter, name='unsubscribe'),
    path('business/', views.BusinessView.as_view(), name='business'),

]
