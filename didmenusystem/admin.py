from django.contrib import admin
from .models import PhoneRecord, States, Carrier, ClientInfo, ClientPseudoCID, PseudoFile, NewOrderInfo, NewOrderPseudoCID, NewPseudoCID, NewClientInfo, ClientList, ClientListData

# Register your models here.
admin.site.register(PhoneRecord)
admin.site.register(States)
admin.site.register(Carrier)
admin.site.register(ClientInfo)
admin.site.register(ClientPseudoCID)
admin.site.register(PseudoFile)
admin.site.register(NewOrderInfo)
admin.site.register(NewOrderPseudoCID)
admin.site.register(NewPseudoCID)
admin.site.register(NewClientInfo)
admin.site.register(ClientList)
admin.site.register(ClientListData)