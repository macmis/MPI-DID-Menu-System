from django.urls import path
from . import views

# URLConf
urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('edit_lastuse_date/<int:pseudo_cid>/', views.edit_lastuse_date, name='edit_lastuse_date'),
    path('pseudoCID/<int:pseudo>', views.pseudo_record, name='pseudoCID'),
    path('PseudoFile-Delete/', views.delete_pseudoCID, name='delete_pseudoCID'),
    path('PseudoFile-Delete-Results/', views.delete_results, name='Delete_Results'),
    path('PseudoFile-Delete-Confirm/', views.delete_confirm, name='Delete_Confirm'),
    path('PseudoFile-Delete-Create/', views.Create_Del_PseudoFile, name='Create_Del_PseudoFile'),
    path('add_pseudoCID/', views.add_pseudoCID, name='add_pseudoCID'),
    path('DID_OrderForm-1/', views.Create_DIDOrdrForm1, name='DID_OrderForm-1'),
    path('DID_OrderForm-1a/', views.Create_DIDOrdrForm1a, name='DID_OrderForm-1a'),
    path('DID_OrderForm-2/', views.Create_DIDOrdrForm2, name='DID_OrderForm-2'),
    path('DID_OrderForm-2a/', views.Create_DIDOrdrForm2a, name='DID_OrderForm-2a'),
    path('DID_OrderForm-3/', views.Create_DIDOrdrForm3, name='DID_OrderForm-3'),
    path('DID_OrderForm-4/', views.Create_DIDOrdrForm4, name='DID_OrderForm-4'),
    path('DID_OrderForm-5/', views.Create_DIDOrdrForm5, name='DID_OrderForm-5'),
    path('getSelState_Counts/', views.GetDID_OrderFormInfo, name='getSelState_Counts'),
    path('DID_OrderForm/', views.DID_OrderForm, name='DID_OrderForm'),
    path('DIDOrderFrm_Results/', views.DIDOrderFrm_Results, name='DIDOrderForm_Results'),
    path('OrderForm-Load/', views.Load_DID_Order, name='Load_DIDOrder'),
    path('PseudoFile-Add/', views.Create_Add_PseudoFile, name='Create_AddPseudoFile'),
    path('Search_Results/', views.SearchResults, name='Search_Results'),
    path('PseudoCID_Export/', views.Export_PseudoCID, name='ExportPseudoCID'),

    # Import URLs for new models
    path('ImportCSV_ClientList/', views.ImportCSV_ClientList, name='ImportCSV_ClientList'),
    path('ImportCSV_ClientListData/', views.ImportCSV_ClientListData, name='ImportCSV_ClientListData'),
    path('ImportCSV_NewOrdertList/', views.ImportCSV_NewOrderList, name='ImportCSV_NewOrderList'),
    path('ImportCSV_NewOrdertListData/', views.ImportCSV_NewOrderListData, name='ImportCSV_NewOrderListData'),
    path('ImportCSV_MPIPseudoCIDs/', views.ImportCSV_MPIPseudoCIDs, name='ImportCSV_MPIPseudoCIDs'),
    path('ImportCSV_MPIClients/', views.ImportCSV_MPIClients, name='ImportCSV_MPIClients'),    
    
    # Remove the following urls once new updates are in production
    #path('ImportCSV_ClientInfo/', views.ImportCSV_ClientInfo, name='ImportCSV_ClientInfo'),
    #path('ImportCSV_CientPseudoCID/', views.ImportCSV_CientPseudoCID, name='ImportCSV_CientPseudoCID'),
    #path('Reset_InActives/', views.ResetInActives, name='Reset_InActives'),
    
    #path('Download_PseudoCID/', views.PseudoCID_CSV_Download, name='PseudoCID_CSV_Download'),

    # # Test function used to review and test `form`. Remove once testing complete
    # path('addnew/', views.addnew, name='addnew'),
]