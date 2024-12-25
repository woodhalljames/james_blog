from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Author, Post, PostRevision, NewsletterSubscriber

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
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_published', 'published_at', 
                   'view_count', 'like_count']
    list_filter = ['is_published', 'created_at', 'published_at', 'author']
    search_fields = ['title', 'content', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'published_at'
    
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