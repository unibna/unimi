# Generated by Django 3.2.8 on 2021-11-27 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_store_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iteamextra',
            name='image',
            field=models.ImageField(blank=True, default='store/item_extra/default-extra.png', null=True, upload_to='store/item_extra/'),
        ),
        migrations.AlterField(
            model_name='item',
            name='image',
            field=models.ImageField(blank=True, default='store/item/default-item.png', null=True, upload_to='store/item/'),
        ),
    ]
