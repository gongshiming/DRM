# Generated by Django 2.2.7 on 2019-12-18 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Owner', '0008_product_product_authorization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_authorization',
            field=models.BooleanField(),
        ),
    ]
