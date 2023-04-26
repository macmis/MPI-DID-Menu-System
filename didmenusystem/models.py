from django.db import models
from django.db.models import Count
from django.utils.translation import gettext as _


# List of all US states for DID Order Form
class States(models.Model):
    StateName =  models.CharField(max_length=50)
    StateAbrv = models.CharField(max_length=2, null=True)
    
    def __str__(self):
        return(f"{self.StateAbrv} {self.StateName}")


# List of Carriers to order DID's from
class Carrier(models.Model):
    CarrierName =  models.CharField(max_length=35)
    CarrierCode = models.CharField(max_length=3, null=True)
    CarrierAbrv = models.CharField(max_length=3)
    
    def __str__(self):
        return(f"{self.CarrierName} {self.CarrierCode} {self.CarrierAbrv}")

    
# List of all PseudoCIDs and Client info. Linked with 'ClientPseudoCID'
class ClientInfo(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('DELETE', 'Delete'),
    )
    PseudoCID = models.CharField(max_length=10)
    Client_Description = models.CharField(max_length=60)
    Client_Code = models.CharField(max_length=8)
    PubCode = models.CharField(max_length=4, blank=True)
    Sales_Type = models.CharField(max_length=1)
    VoiceMail = models.CharField(max_length=4)
    InBnd_TranNo =  models.CharField(max_length=10)
    Carrier = models.CharField(max_length=30)
    Status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='Pending')
    PR_Date = models.DateField(blank=True)
    LastUse_Date = models.DateField(blank=True, null=True)
    DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    LeadFileID = models.CharField(max_length=30, blank=True, null=True)
    Notes = models.CharField(max_length=60, blank=True, null=True)
    
    class Meta:
        db_table = 'ClientInfo'

    # Function - Count the number of records in ClientPseudoCID for this PseudoCID
    def update_did_cnt(self):
        count = ClientPseudoCID.objects.filter(PseudoCID=self.PseudoCID).count()

        # Update the DID_CNT field for this ClientInfo object
        self.DID_CNT = count
        self.save()

    def __str__(self):
        return(f"{self.PseudoCID} {self.Client_Description} {self.PR_Date} {self.Status} {self.LastUse_Date} {self.DID_CNT}")


# List of all PseudoCIDs and DIDs within. Linked with 'PseudoFile'
class ClientPseudoCID(models.Model):
    PseudoCID = models.CharField(max_length=10)
    PhoneNo =  models.CharField(max_length=10)
    PhnNo_Loc = models.CharField(max_length=2)
    Status = models.CharField(max_length=1)
    LeadFileID = models.CharField(max_length=30, null=True)
    Deact_Date = models.DateField(blank=True)
    # Define a foreign key to ClientInfo table based on PseudoCID field
    client_info = models.ForeignKey(ClientInfo, on_delete=models.CASCADE, related_name='client_pseudocids', null=True, default=None)
    
    def __str__(self):
        return(f"{self.PseudoCID} {self.PhoneNo} {self.PhnNo_Loc} {self.Status} {self.Deact_Date}")


# PseudoFile used to upload to Randy's website
class PseudoFile(models.Model):
    ACTION_CHOICES = (
        ('ADD', 'Add'),
        ('UPDATE', 'Update'),
        ('DEACTIVATE', 'Deactivate'),
        ('ACTIVATE', 'Activate'),
        ('DELETE', 'Delete'),
    )
    YES_NO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
    )
    PseudoCID =  models.CharField(max_length=10)
    PhoneNo = models.CharField(max_length=10)
    Client_Code = models.CharField(max_length=8)
    InBnd_TranNo = models.CharField(max_length=10)
    Action = models.CharField(max_length=11, choices=ACTION_CHOICES, default='DELETE')
    LeadFileID = models.CharField(max_length=30, null=True)
    Deact_Date = models.DateField(blank=True)
    OkToArchive = models.CharField(max_length=1, choices=YES_NO_CHOICES, default='N')
    # Define a foreign key to ClientPseudoCID table based on PseudoCID field
    client_pseudocid = models.ForeignKey(ClientPseudoCID, on_delete=models.CASCADE, related_name='pseudo_files', null=True, default=None)
    

# Infomation used to create new order form.  Linked with 'NewOrderPseudoCID'
class NewOrderInfo(models.Model):
    YES_NO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
        ('P', 'Pending'),
    )
    LeadFileID = models.CharField(max_length=30, null=True)
    Carrier = models.CharField(max_length=30)
    Total_DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    Sel_States = models.CharField(max_length=160)
    PR_Date = models.DateField(blank=True)
    FileName = models.CharField(max_length=20, blank=True)
    OrderComplete = models.CharField(max_length=1, choices=YES_NO_CHOICES, default='P') 
       
    def __str__(self):
        return(f"{self.LeadFileID} {self.Carrier} {self.Total_DID_CNT} {self.Sel_States} {self.PR_Date} {self.FileName}")


# Infomation used to create new order form
class NewOrderPseudoCID(models.Model):
    LeadFileID = models.CharField(max_length=30, null=True)
    PseudoCID =  models.CharField(max_length=10)    
    Client_Description = models.CharField(max_length=60)
    DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    order_info = models.ForeignKey(NewOrderInfo, on_delete=models.CASCADE, related_name='pseudo_cids', null=True, default=None)
        
    def __str__(self):
        return(f"{self.LeadFileID} {self.PseudoCID} {self.Client_Description}")


# List of Active Clients to assign to NEW PseudoCIDs
class NewClientInfo(models.Model):
    Client_Description =  models.CharField(max_length=60)
    Sales_Type = models.CharField(max_length=1)    
    Client_Code = models.CharField(max_length=8)
    PubCode = models.CharField(max_length=4, blank=True)
    InBnd_TranNo =  models.CharField(max_length=10)
        
    def __str__(self):
        return(f"{self.Client_Description} {self.Sales_Type} {self.Client_Code} {self.PubCode} {self.InBnd_TranNo}")


# Unassigned PseudoCID's 
class NewPseudoCID(models.Model):
    PseudoCID =  models.CharField(max_length=10)
    Sales_Type = models.CharField(max_length=1)    
    Carrier = models.CharField(max_length=30)    
        
    def __str__(self):
        return(f"{self.PseudoCID} {self.Sales_Type} {self.Carrier}")


# REMOVE THIS TABLE ONCE ALL DATA HAS BEEN REFORMATTED AND UPLOADED TO NEW TABLES
class PhoneRecord(models.Model):
    #created_at = models.DateTimeField(auto_now_add=True)
    PhoneNo =  models.CharField(max_length=10)
    PseudoCID = models.CharField(max_length=10)
    TFN_PrimaryNo = models.CharField(max_length=3)
    DID_Location = models.CharField(max_length=3, null=True)
    Sales_Type = models.CharField(max_length=1)
    PubCode = models.CharField(max_length=4)
    ClientCode = models.CharField(max_length=8)
    Client_Description = models.CharField(max_length=60)
    VoiceMail = models.CharField(max_length=4)
    Carrier = models.CharField(max_length=30)
    PR_status = models.CharField(max_length=1)
    PR_Date = models.CharField(max_length=10)
    LastUse_Date = models.CharField(max_length=10)
    Notes = models.CharField(max_length=60, null=True)

    def __str__(self):
        return(f"{self.PseudoCID} {self.PhoneNo} {self.Client_Description} {self.PR_status} {self.PR_Date}")
    

