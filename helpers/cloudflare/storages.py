from storages.backends.s3 import S3Storage

class StaticFileStorage(S3Storage):
    location = "static"
    
    def _normalize_name(self, name):
        # Prevent bucket name duplication
        if name.startswith(self.bucket_name + '/'):
            name = name[len(self.bucket_name) + 1:]
        return super()._normalize_name(name)

class MediaFileStorage(S3Storage):
    location = "media"
    
    def _normalize_name(self, name):
        # Prevent bucket name duplication
        if name.startswith(self.bucket_name + '/'):
            name = name[len(self.bucket_name) + 1:]
        return super()._normalize_name(name)
