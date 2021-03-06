# Generated by Django 3.2.8 on 2021-11-19 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20211120_0130'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[['created', 'created'], ['confirm', 'confirm'], ['doing', 'doing'], ['delivery', 'delivery'], ['done', 'done']], default='created', max_length=32),
        ),
        migrations.AlterField(
            model_name='orderstatus',
            name='status',
            field=models.CharField(choices=[['created', 'created'], ['confirm', 'confirm'], ['doing', 'doing'], ['delivery', 'delivery'], ['done', 'done']], max_length=32),
        ),
    ]
