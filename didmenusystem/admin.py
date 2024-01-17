from django.contrib import admin
from .models import States, Carrier, PseudoFile, ClientList, ClientListData, NewOrderList, NewOrderListData, MPIPseudoCIDs, MPIClients, ClientListArchive

# Register your models here.
admin.site.register(States)
admin.site.register(Carrier)
admin.site.register(PseudoFile)
admin.site.register(ClientList)
admin.site.register(ClientListData)
admin.site.register(NewOrderList)
admin.site.register(NewOrderListData)
admin.site.register(MPIPseudoCIDs)
admin.site.register(MPIClients)
admin.site.register(ClientListArchive)