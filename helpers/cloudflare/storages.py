from storages.backends.s3 import S3Storage

class StaticFileStorage(S3Storage):
    location = "static"
    
    def url(self, name, parameters=None, expire=None):
        # Clean the name to ensure proper formatting
        if self.location:
            name = f"{self.location}/{name}"
            
        url = f"{self.endpoint_url}/{self.bucket_name}/{name}"
        return url

class MediaFileStorage(S3Storage):
    location = "media"
    
    def url(self, name, parameters=None, expire=None):
        # Clean the name to ensure proper formatting
        if self.location:
            name = f"{self.location}/{name}"
            
        url = f"{self.endpoint_url}/{self.bucket_name}/{name}"
        return url
