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
# Old as of 7/19/23 - Remove once code is formatted to use `ClientList`
class ClientInfo(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('INACTIVE', 'In-Active'),
    )
    PseudoCID = models.CharField(max_length=10)
    Client_Description = models.CharField(max_length=60)
    Client_Code = models.CharField(max_length=8)
    PubCode = models.CharField(max_length=4, blank=True)
    Sales_Type = models.CharField(max_length=1)
    VoiceMail = models.CharField(max_length=4)
    InBnd_TranNo =  models.CharField(max_length=10)
    Carrier = models.CharField(max_length=30)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    PR_Date = models.DateField(blank=True, null=True)
    LastUse_Date = models.DateField(blank=True, null=True, default='')
    DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    LeadFileID = models.CharField(max_length=30, blank=True, null=True)
    Notes = models.CharField(max_length=60, blank=True, null=True, default='')
    
    class Meta:
        db_table = 'ClientInfo'
        # Define the composite primary key --- Use line below when commented out Reference for ForeignKey in `ClientPseudoCID` is working
        #unique_together = ('PseudoCID', 'LeadFileID')

    # Function - Count the number of records in ClientPseudoCID for this PseudoCID
    def update_did_cnt(self):
        count = ClientPseudoCID.objects.filter(PseudoCID=self.PseudoCID).count()
        
        # Update the DID_CNT field for this ClientInfo object
        self.DID_CNT = count
        self.save()

    def __str__(self):
        return(f"{self.PseudoCID} {self.Client_Description} {self.PR_Date} {self.Status} {self.LastUse_Date} {self.DID_CNT} {self.LeadFileID}")


# List of all PseudoCIDs and DIDs within. Linked with 'PseudoFile'
# Old as of 7/19/23 - Remove once code is formatted to use `ClientListData`
class ClientPseudoCID(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('INACTIVE', 'In-Active'),
    )
    PseudoCID = models.CharField(max_length=10)
    PhoneNo =  models.CharField(max_length=10)
    PhnNo_Loc = models.CharField(max_length=2)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')    
    LeadFileID = models.CharField(max_length=30, null=True)
    Deact_Date = models.DateField(blank=True, null=True, default=None)

    # Reference the composite primary key of ClientInfo model    
    #client_info = models.ForeignKey(ClientInfo, on_delete=models.CASCADE, related_name='client_pseudocids', to_field=['LeadFileID', 'PseudoCID'], null=True, default=None)

    # Uncomment this once table record load complete and successful
    client_info = models.ForeignKey(ClientInfo, on_delete=models.CASCADE, related_name='client_pseudocids', null=True, default=None)
    
    def __str__(self):
        return(f"{self.PseudoCID} {self.PhoneNo} {self.PhnNo_Loc} {self.Status} {self.Deact_Date}")

# Active List of PseudoCIDs with assigned Client info. Linked with 'ClientListData'
class ClientList(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('INACTIVE', 'In-Active'),
    )
    PseudoCID = models.CharField(max_length=10)
    Client_Description = models.CharField(max_length=60)
    Client_Code = models.CharField(max_length=8)
    PubCode = models.CharField(max_length=4, blank=True)
    Sales_Type = models.CharField(max_length=1)
    VoiceMail = models.CharField(max_length=4)
    InBnd_TranNo =  models.CharField(max_length=10)
    Carrier = models.CharField(max_length=30)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    PR_Date = models.DateField(blank=True, null=True)
    LastUse_Date = models.DateField(blank=True, null=True, default=None)
    DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    Notes = models.CharField(max_length=60, blank=True, null=True, default='')

    # Function - Count the number of records in `ClientListData` for each 'PseudoCID'
    def update_did_cnt(self):
        count = ClientListData.objects.filter(PseudoCID=self).count()        
        
        # Update the DID_CNT field for this ClientList object
        self.DID_CNT = count
        self.save()

    def __str__(self):
        return(f"{self.PseudoCID} {self.Client_Description} {self.PR_Date} {self.Status} {self.LastUse_Date} {self.DID_CNT}")

# List of all PseudoCIDs and DIDs within. Linked to model `ClientList`
class ClientListData(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('INACTIVE', 'In-Active'),
    )
    PseudoCID = models.ForeignKey(ClientList, on_delete=models.CASCADE)    
    PhoneNo = models.CharField(max_length=10)
    PhnNo_Loc = models.CharField(max_length=2)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')    
    LeadFileID = models.CharField(max_length=30, null=True)
    Deact_Date = models.DateField(blank=True, null=True, default='')

    def __str__(self):
        return(f"{self.PseudoCID} {self.PhoneNo} {self.PhnNo_Loc} {self.Status} {self.LeadFileID} {self.Deact_Date}")


# PseudoFile used to upload to Randy's website & Create Carrier Cancelation Form
# Move this model below `MPIClients` once code is formatted to use new model names
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
    PhnNo_Loc = models.CharField(max_length=2, blank=True)
    Client_Code = models.CharField(max_length=8)
    InBnd_TranNo = models.CharField(max_length=10)
    Action = models.CharField(max_length=11, choices=ACTION_CHOICES, default='DELETE')
    LeadFileID = models.CharField(max_length=30, null=True)
    FileName = models.CharField(max_length=25, blank=True)
    Carrier = models.CharField(max_length=30, blank=True)    
    Deact_Date = models.DateField(blank=True, null=True, default='')
    OkToArchive = models.CharField(max_length=1, choices=YES_NO_CHOICES, default='N')
    # Define a foreign key to ClientPseudoCID table based on PseudoCID field
    client_pseudocid = models.ForeignKey(ClientPseudoCID, on_delete=models.CASCADE, related_name='pseudo_files', null=True, default=None)

    def __str__(self):
        return(f"{self.PseudoCID} {self.PhoneNo} {self.Client_Code} {self.InBnd_TranNo} {self.Action} {self.LeadFileID} {self.Deact_Date} {self.OkToArchive}")


# Infomation used to create new order form.  Linked with 'NewOrderPseudoCID'
# Old as of 7/19/23 - Remove once code is formatted to use `NewOrderList`
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
    FileName = models.CharField(max_length=25, blank=True)
    OrderComplete = models.CharField(max_length=1, choices=YES_NO_CHOICES, default='P') 
       
    def __str__(self):
        return(f"{self.LeadFileID} {self.Carrier} {self.Total_DID_CNT} {self.Sel_States} {self.PR_Date} {self.FileName}")


# Infomation used to create new order form
# Old as of 7/19/23 - Remove once code is formatted to use `NewOrderListData`
class NewOrderPseudoCID(models.Model):
    LeadFileID = models.CharField(max_length=30, null=True)
    PseudoCID =  models.CharField(max_length=10)    
    Client_Description = models.CharField(max_length=60)
    Sales_Type = models.CharField(max_length=1, null=True)    
    Client_Code = models.CharField(max_length=8, null=True)
    PubCode = models.CharField(max_length=4, blank=True)
    InBnd_TranNo =  models.CharField(max_length=10, null=True)
    VoiceMail = models.CharField(max_length=4, null=True)
    DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    order_info = models.ForeignKey(NewOrderInfo, on_delete=models.CASCADE, related_name='pseudo_cids', null=True, default=None)
        
    def __str__(self):
        return(f"{self.LeadFileID} {self.PseudoCID} {self.Client_Description} {self.Sales_Type} {self.Client_Code} {self.PubCode} {self.InBnd_TranNo} {self.VoiceMail} {self.DID_CNT}")

# Infomation used to create new order form.  Linked with 'NewOrderListData'
class NewOrderList(models.Model):
    YES_NO_CHOICES = (
        ('Y', 'Yes'),
        ('N', 'No'),
        ('P', 'Pending'),
    )
    LeadFileID = models.CharField(max_length=30, null=True)
    Carrier = models.CharField(max_length=30)
    Total_DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    Sel_States = models.CharField(max_length=160)
    PR_Date = models.DateField(blank=True, null=True)    
    FileName = models.CharField(max_length=25, blank=True)
    OrderComplete = models.CharField(max_length=1, choices=YES_NO_CHOICES, default='P') 
       
    def __str__(self):
        return(f"{self.LeadFileID} {self.Carrier} {self.Total_DID_CNT} {self.Sel_States} {self.PR_Date} {self.FileName}")

# Infomation used to create new order form
class NewOrderListData(models.Model):
    LeadFileID = models.CharField(max_length=30, null=True)
    PseudoCID =  models.CharField(max_length=10)    
    Client_Description = models.CharField(max_length=60)
    Sales_Type = models.CharField(max_length=1, null=True)    
    Client_Code = models.CharField(max_length=8, null=True)
    PubCode = models.CharField(max_length=4, blank=True)
    InBnd_TranNo =  models.CharField(max_length=10, null=True)
    VoiceMail = models.CharField(max_length=4, null=True)
    DID_CNT = models.IntegerField(default=0, blank=True, null=True)
    order_list = models.ForeignKey(NewOrderList, on_delete=models.CASCADE, related_name='pseudo_cids', null=True, default=None)
        
    def __str__(self):
        return(f"{self.LeadFileID} {self.PseudoCID} {self.Client_Description} {self.Sales_Type} {self.Client_Code} {self.PubCode} {self.InBnd_TranNo} {self.VoiceMail} {self.DID_CNT}")


# List of Active Clients to assigned to MPI PseudoCIDs
# Old as of 7/19/23 - Remove once code is formatted to use `MPIClients`
class NewClientInfo(models.Model):
    Client_Description =  models.CharField(max_length=60)
    Sales_Type = models.CharField(max_length=1)    
    Client_Code = models.CharField(max_length=8)
    PubCode = models.CharField(max_length=4, blank=True)
    InBnd_TranNo =  models.CharField(max_length=10)
    VoiceMail = models.CharField(max_length=4, null=True)    
        
    def __str__(self):
        return(f"{self.Client_Description} {self.Sales_Type} {self.Client_Code} {self.PubCode} {self.InBnd_TranNo} {self.VoiceMail}")


# List of all MPI PseudoCID's 
# Old as of 7/19/23 - Remove once code is formatted to use `MPIPseudoCIDs`
class NewPseudoCID(models.Model):
    STATUS_CHOICES = (
        ('A', 'ACTIVE'),
        ('I', 'INACTIVE'),
        ('X', 'UNASSIGNED'),        
    )
    
    PseudoCID =  models.CharField(max_length=10)
    Sales_Type = models.CharField(max_length=1)    
    Carrier = models.CharField(max_length=30)
    Status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='I')    
        
    def __str__(self):
        return(f"{self.PseudoCID} {self.Sales_Type} {self.Carrier} {self.Status}")



# List of all MPI PseudoCID's 
class MPIPseudoCIDs(models.Model):
    STATUS_CHOICES = (
        ('A', 'ACTIVE'),
        ('I', 'INACTIVE'),
        ('X', 'UNASSIGNED'),        
    )
    
    PseudoCID =  models.CharField(max_length=10)
    Sales_Type = models.CharField(max_length=1)    
    Carrier = models.CharField(max_length=30)
    Status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='I')    
        
    def __str__(self):
        return(f"{self.PseudoCID} {self.Sales_Type} {self.Carrier} {self.Status}")

# List of Active Clients to assigned to MPI PseudoCIDs
class MPIClients(models.Model):
    Client_Description =  models.CharField(max_length=60)
    Sales_Type = models.CharField(max_length=1)    
    Client_Code = models.CharField(max_length=8)
    PubCode = models.CharField(max_length=4, blank=True)
    InBnd_TranNo =  models.CharField(max_length=10)
    VoiceMail = models.CharField(max_length=4, null=True)    
        
    def __str__(self):
        return(f"{self.Client_Description} {self.Sales_Type} {self.Client_Code} {self.PubCode} {self.InBnd_TranNo} {self.VoiceMail}")


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
    

