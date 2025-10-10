from django.core.mail import send_mail
from django.conf import settings

try:
    send_mail(
        'Test Email',
        'This is a test email from Django.',
        settings.DEFAULT_FROM_EMAIL,
        ['your-test-email@example.com'],
        fail_silently=False,
    )
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error: {e}")