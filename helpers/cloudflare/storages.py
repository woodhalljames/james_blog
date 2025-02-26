from storages.backends.s3boto3 import S3Boto3Storage

class StaticFileStorage(S3Boto3Storage):
    location = "static"
    querystring_auth = False  # Disable authentication
    
    def url(self, name, parameters=None, expire=None):
        # Custom URL generation for static files
        name = self._normalize_name(self._clean_name(name))
        url = f"{self.endpoint_url}/{self.bucket_name}/{self.location}/{name}"
        return url.replace('https://', 'https://')  # Make sure it's https

class MediaFileStorage(S3Boto3Storage):
    location = "media"
    querystring_auth = False  # Disable authentication
    
    def url(self, name, parameters=None, expire=None):
        # Custom URL generation for media files
        name = self._normalize_name(self._clean_name(name))
        url = f"{self.endpoint_url}/{self.bucket_name}/{self.location}/{name}"
        return url.replace('https://', 'https://')  # Make sure it's https
