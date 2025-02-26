from storages.backends.s3 import S3Storage

class StaticFileStorage(S3Storage):
    location = "static"
    
    def __init__(self, **settings):
        # Ensure we're using authentication
        settings['querystring_auth'] = True
        # Set very long expiration (7 days)
        settings['querystring_expire'] = 60 * 60 * 24 * 7
        super().__init__(**settings)

class MediaFileStorage(S3Storage):
    location = "media"
    
    def __init__(self, **settings):
        # Ensure we're using authentication
        settings['querystring_auth'] = True
        # Set very long expiration (7 days)
        settings['querystring_expire'] = 60 * 60 * 24 * 7
        super().__init__(**settings)
