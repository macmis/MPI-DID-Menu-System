# Generated by Django 4.1.7 on 2023-07-27 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didmenusystem', '0003_alter_clientlistdata_pseudocid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientlistdata',
            name='PseudoCID',
            field=models.CharField(max_length=10),
        ),
    ]
