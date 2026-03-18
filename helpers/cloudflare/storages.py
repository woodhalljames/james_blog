from storages.backends.s3 import S3Storage
from django.conf import settings


class CloudflareStorage(S3Storage):
    """
    UPDATED: Base storage class for Cloudflare R2 with proper configuration handling
    
    This storage class now properly initializes with settings from Django's STORAGES configuration
    """
    
    def __init__(self, **kwargs):
        # If no kwargs provided, get from settings
        if not kwargs:
            # Get the storage config from STORAGES setting
            storage_config = getattr(settings, 'CLOUDFLARE_R2_CONFIG_OPTIONS', {})
            kwargs = storage_config.copy()
        
        # Explicitly remove security token which R2 doesn't support
        kwargs['security_token'] = None
        
        # Initialize the parent class with our adjusted settings
        super().__init__(**kwargs)
        
    def get_default_settings(self):
        """Override to ensure security_token is always None for Cloudflare R2"""
        defaults = super().get_default_settings()
        defaults['security_token'] = None
        return defaults


class StaticFileStorage(CloudflareStorage):
    """Storage class for static files in Cloudflare R2"""
    location = "static"
    
    def __init__(self, **kwargs):
        if not kwargs:
            storage_config = getattr(settings, 'CLOUDFLARE_R2_CONFIG_OPTIONS', {})
            kwargs = storage_config.copy()
        super().__init__(**kwargs)


class MediaFileStorage(CloudflareStorage):
    """Storage class for media files in Cloudflare R2"""
    location = "media"
    
    def __init__(self, **kwargs):
        if not kwargs:
            storage_config = getattr(settings, 'CLOUDFLARE_R2_CONFIG_OPTIONS', {})
            kwargs = storage_config.copy()
        super().__init__(**kwargs)