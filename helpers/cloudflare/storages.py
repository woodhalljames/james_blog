
from storages.utils import setting
from storages.backends.s3 import S3Storage

class CloudflareStorage(S3Storage):
    """Base storage class for Cloudflare R2"""
    
    def __init__(self, **settings):
        # Explicitly remove security token which R2 doesn't support
        settings['security_token'] = None
        # Ensure proper file overwrite behavior
        settings['file_overwrite'] = False
        # Initialize the parent class with our adjusted settings
        super().__init__(**settings)
        
    def get_default_settings(self):
        # Get default settings from parent class
        defaults = super().get_default_settings()
        # Ensure security_token is always None for Cloudflare R2
        defaults['security_token'] = None
        defaults['file_overwrite'] = False
        return defaults
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """Override to ensure proper URL generation"""
        if name:
            # Clean the name to avoid double slashes
            name = name.lstrip('/')
        return super().url(name, parameters, expire, http_method)


class StaticFileStorage(CloudflareStorage):
    """Storage class for static files in Cloudflare R2"""
    location = "static"


class MediaFileStorage(CloudflareStorage):
    """Storage class for media files in Cloudflare R2"""
    location = "media"