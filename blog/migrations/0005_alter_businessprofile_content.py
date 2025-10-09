# blog/migrations/0004_add_content_field.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_businessprofile_summernoteattachment_and_more'),
    ]

    operations = [
        # Add as regular TextField first to avoid bleach issues during migration
        migrations.AddField(
            model_name='businessprofile',
            name='content',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Your professional profile content - add your summary, experience, projects, education, etc.'
            ),
        ),
    ]