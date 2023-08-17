# Generated by Django 4.1.7 on 2023-08-10 22:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('didmenusystem', '0009_alter_clientlist_lastuse_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewOrderList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('LeadFileID', models.CharField(max_length=30, null=True)),
                ('Carrier', models.CharField(max_length=30)),
                ('Total_DID_CNT', models.IntegerField(blank=True, default=0, null=True)),
                ('Sel_States', models.CharField(max_length=160)),
                ('PR_Date', models.DateField(blank=True)),
                ('FileName', models.CharField(blank=True, max_length=25)),
                ('OrderComplete', models.CharField(choices=[('Y', 'Yes'), ('N', 'No'), ('P', 'Pending')], default='P', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='NewOrderListData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('LeadFileID', models.CharField(max_length=30, null=True)),
                ('PseudoCID', models.CharField(max_length=10)),
                ('Client_Description', models.CharField(max_length=60)),
                ('Sales_Type', models.CharField(max_length=1, null=True)),
                ('Client_Code', models.CharField(max_length=8, null=True)),
                ('PubCode', models.CharField(blank=True, max_length=4)),
                ('InBnd_TranNo', models.CharField(max_length=10, null=True)),
                ('VoiceMail', models.CharField(max_length=4, null=True)),
                ('DID_CNT', models.IntegerField(blank=True, default=0, null=True)),
                ('order_list', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pseudo_cids', to='didmenusystem.neworderlist')),
            ],
        ),
    ]
