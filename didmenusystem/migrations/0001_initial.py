# Generated by Django 4.1.7 on 2023-03-02 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PhoneRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('PhoneNo', models.CharField(max_length=10)),
                ('PseudoCID', models.CharField(max_length=10)),
                ('TFN_PrimaryNo', models.CharField(max_length=3)),
                ('DID_Location', models.CharField(max_length=3)),
                ('Sales_Type', models.CharField(max_length=1)),
                ('PubCode', models.CharField(max_length=4)),
                ('ClientCode', models.CharField(max_length=8)),
                ('Client_Description', models.CharField(max_length=60)),
                ('VoiceMail', models.CharField(max_length=4)),
                ('Carrier', models.CharField(max_length=30)),
                ('PR_status', models.CharField(max_length=1)),
                ('PR_Date', models.CharField(max_length=10)),
                ('LastUse_Date', models.CharField(max_length=10)),
                ('Notes', models.CharField(max_length=60)),
            ],
        ),
    ]
