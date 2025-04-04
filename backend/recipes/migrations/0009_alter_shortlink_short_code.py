# Generated by Django 3.2.16 on 2025-04-04 17:46

from django.db import migrations, models

import shortuuid.main


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20250405_0039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shortlink',
            name='short_code',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, max_length=22, unique=True, verbose_name='Короткий код'),
        ),
    ]
