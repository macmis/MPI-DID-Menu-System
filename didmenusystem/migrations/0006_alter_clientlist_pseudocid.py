# Generated by Django 4.1.7 on 2023-08-03 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('didmenusystem', '0005_alter_clientlistdata_pseudocid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientlist',
            name='PseudoCID',
            field=models.CharField(max_length=10),
        ),
    ]
