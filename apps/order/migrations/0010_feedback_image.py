# Generated by Django 3.2.8 on 2021-11-25 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0009_feedback_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='order/feedback/'),
        ),
    ]
