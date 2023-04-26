# Generated by Django 4.1.7 on 2023-04-06 19:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('didmenusystem', '0017_alter_clientinfo_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientpseudocid',
            name='client_info',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='client_pseudocids', to='didmenusystem.clientinfo'),
        ),
        migrations.AddField(
            model_name='pseudofile',
            name='client_pseudocid',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pseudo_files', to='didmenusystem.clientpseudocid'),
        ),
    ]
