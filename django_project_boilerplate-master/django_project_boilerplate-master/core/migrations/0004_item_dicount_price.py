# Generated by Django 3.0.8 on 2020-07-28 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_item_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='dicount_price',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
