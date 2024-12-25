# blog/context_processors.py

from .models import Author

def author_profile(request):
    """
    Adds author profile information to all templates
    """
    try:
        author = Author.objects.first()  # Assuming you have one main author
        return {
            'profile_author': author
        }
    except Author.DoesNotExist:
        return {
            'profile_author': None
        }