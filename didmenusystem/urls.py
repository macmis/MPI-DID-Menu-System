from django.urls import path
from . import views

# URLConf
urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('pseudoCID/<int:pseudo>', views.pseudo_record, name='pseudoCID'),
    path('delete_pseudoCID/', views.delete_pseudoCID, name='delete_pseudoCID'),
    path('Delete_Results/', views.delete_results, name='Delete_Results'),
    path('Delete_Confirm/', views.delete_confirm, name='Delete_Confirm'),
    path('add_pseudoCID/', views.add_pseudoCID, name='add_pseudoCID'),
    path('DID_OrderForm-1/', views.Create_DIDOrdrForm1, name='DID_OrderForm-1'),
    path('DID_OrderForm-2/', views.Create_DIDOrdrForm2, name='DID_OrderForm-2'),
    path('DID_OrderForm-3/', views.Create_DIDOrdrForm3, name='DID_OrderForm-3'),
    path('DID_OrderForm-4/', views.Create_DIDOrdrForm4, name='DID_OrderForm-4'),
    path('DID_OrderForm-5/', views.Create_DIDOrdrForm5, name='DID_OrderForm-5'),
    path('getSelState_Counts/', views.GetDID_OrderFormInfo, name='getSelState_Counts'),
    path('DID_OrderForm/', views.DID_OrderForm, name='DID_OrderForm'),    
    path('DIDOrderFrm_Results/', views.DIDOrderFrm_Results, name='DIDOrderForm_Results'),
    path('Load_DIDOrder/', views.Load_DIDOrder, name='Load_DIDOrder'),
    path('Search_Results/', views.SearchResults, name='Search_Results'),
    # Test function used to review and test `form`. Remove once testing complete
    path('addnew/', views.addnew, name='addnew'),
]