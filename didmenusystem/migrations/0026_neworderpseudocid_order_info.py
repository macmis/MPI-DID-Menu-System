# Generated by Django 4.1.7 on 2023-04-18 22:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('didmenusystem', '0025_newclientinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='neworderpseudocid',
            name='order_info',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pseudo_cids', to='didmenusystem.neworderinfo'),
        ),
    ]
