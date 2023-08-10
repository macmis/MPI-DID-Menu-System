from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotAllowed, FileResponse
from .forms import SignUpForm, AddPseudoCIDForm, NewOrderInfoForm, NewOrderPseudoCIDForm
from datetime import datetime, timedelta
from .models import PhoneRecord, States, Carrier, ClientInfo, ClientPseudoCID, PseudoFile, NewOrderInfo, NewOrderPseudoCID, NewPseudoCID, NewClientInfo, ClientList, ClientListData
from io import BytesIO
from zipfile import ZipFile
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import uuid, itertools, csv, random
import pandas as pd


# Create your views here.
def home(request):
    # Get list of Client Info and udpate DID counts for each Client
    client_info_list = ClientList.objects.all()
    
    # Update DID count by actual number of DID's per PseudoCID
    if len(client_info_list) > 0:
        for client_info in client_info_list:
            client_info.update_did_cnt()

     # Get selected filter
    sort_option = request.GET.get('sort')
    
    # Check if sort option was selected
    if sort_option:
        filter_selection = sort_option[:16]
        if filter_selection == "split_by_carrier":
            # Only 2 Carriers reside in model `Carrier` - MODIFY CODE IF NUMBER OF SIP CARRIERS INCREASE
            carrier_info_list = Carrier.objects.all()

            # Get values for each record in `carrier_info_list` and assign to variables: Carrier-1, Carrier-2
            carrier1 = carrier_info_list[0] if len(carrier_info_list) >= 1 else None
            carrier2 = carrier_info_list[1] if len(carrier_info_list) >= 2 else None
            
            # Perform filters by user selection
            if sort_option == "split_by_carrier_All":
                client_info_list1 = ClientList.objects.filter(Carrier=carrier1.CarrierName)            
                client_info_list2 = ClientList.objects.filter(Carrier=carrier2.CarrierName)
            elif sort_option == "split_by_carrier_Res":
                client_info_list1 = ClientList.objects.filter(Carrier=carrier1.CarrierName, Sales_Type="R")            
                client_info_list2 = ClientList.objects.filter(Carrier=carrier2.CarrierName, Sales_Type="R")
            elif sort_option == "split_by_carrier_Bus":
                client_info_list1 = ClientList.objects.filter(Carrier=carrier1.CarrierName, Sales_Type="B")
                client_info_list2 = ClientList.objects.filter(Carrier=carrier2.CarrierName, Sales_Type="B")
                
            records_carrier1 = client_info_list1.values('PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier')
            records_carrier2 = client_info_list2.values('PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier')
            records = None

        else:
            filter_selection = sort_option
            if filter_selection == 'sort_by_carrier_All':
                client_info_list = client_info_list.order_by('Carrier')
            elif filter_selection == 'sort_by_carrier_Res':
                client_info_list = client_info_list.filter(Sales_Type="R").order_by('Carrier')
            elif filter_selection == 'sort_by_carrier_Bus':
                client_info_list = client_info_list.filter(Sales_Type="B").order_by('Carrier')
            elif filter_selection == 'sort_by_pseudoCID':
                client_info_list = client_info_list.order_by('PseudoCID')
            elif filter_selection == 'sort_by_prdate':
                client_info_list = client_info_list.order_by('PR_Date')

            records = client_info_list.values('PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status', 'LastUse_Date', 'PR_Date', 'DID_CNT')
            records_carrier1 = None
            records_carrier2 = None
            carrier1 = None
            carrier2 = None
    else:
        records = client_info_list.values('PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status', 'LastUse_Date', 'PR_Date', 'DID_CNT')
        records_carrier1 = None
        records_carrier2 = None
        carrier1 = None
        carrier2 = None
        filter_selection = None        
    
    # Check to see if logging in
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # Authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have Successfully Logged In!")
            return redirect('home')
        else:
            messages.error(request, "Login Unsuccessful, Please Try Again...")
            return redirect('home')
    else:
        return render(request, 'home.html', {'records':records, 'carrier1':carrier1, 'carrier2':carrier2, 'records_carrier1':records_carrier1, 'records_carrier2':records_carrier2, 'filter_selection': filter_selection})

def logout_user(request):
    logout(request)
    messages.success(request, "You Have Successfully Logged Out...")
    return redirect('home')


def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Authenticate and login
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You Have Successfully Registered!")
            return redirect('home')
    else:
        form = SignUpForm()
        return render(request, 'register.html', {'form':form})
    
    return render(request, 'register.html', {'form':form})


def pseudo_record(request, pseudo):
    if request.user.is_authenticated:
        # Fetch the ClientList instance based on the PseudoCID
        client_info = get_object_or_404(ClientList, PseudoCID=pseudo)

        # Use the reverse relation to get related ClientListData instances
        client_pseudocids = client_info.clientlistdata_set.all()

        context = {
            'client_pseudocids': client_pseudocids,
            'client_info': client_info,
        }
        return render(request, 'pseudoCID.html', context)
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')

    
 #   
def add_pseudoCID(request):
    form = AddPseudoCIDForm(request.POST or None)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                add_pseudoCID = form.save()
                messages.success(request, "Record Added...")
                return redirect('home')
            
            return render(request, 'add_pseudoCID.html', {'form':form})
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')
    

# 
def Create_DIDOrdrForm1(request):
    if request.user.is_authenticated:
        # Clean incomplete Order Form records
        order_info = NewOrderInfo.objects.filter(OrderComplete="N")
        for record in order_info:
            order_info.delete()        

        carriers = Carrier.objects.all()
        return render(request, 'DID_OrderForm-1.html', {'carriers': carriers})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')

# Verify if this function is needed? Review modifying urls.py
def Create_DIDOrdrForm1a(request):
    if request.user.is_authenticated:
        return render(request, 'DID_OrderForm-1a.html', {})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')
    
    
# Get amount of DIDs, select non-active PseudoCIDs and assign to clients
def Create_DIDOrdrForm2(request):
    if request.user.is_authenticated:
        curetime = datetime.now()
        NewOrderForm="Y"

        if request.method == 'GET':
            order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
            filename=order_info.FileName
            CarrierName=order_info.Carrier
            NewOrderForm=order_info.OrderComplete
        elif request.method == 'POST':
            # Get PseudoCID type, Sales Type and Carrier
            selected_option = request.POST.get('pseudoCID_options')
            selected_SalesType = request.POST.get('SalesType_options')
            request.session['SalesType'] = selected_SalesType            
            selected_carrier = request.POST.get('selected_carrier')
            # Create LeadFile Name
            CarrierInfo = selected_carrier.split()
            CarrierName = CarrierInfo[0]
            filename = CarrierInfo[2] + "-Order_"
            etime = curetime.strftime("%Y%m%d%S")
            fetime = etime[:8] + "-" + etime[8:]
            filename = filename + fetime

            if not selected_carrier:
                messages.success(request, "No Carrier was selected for Order Form!  Please try again...")
                return redirect('home')
            
            if not selected_SalesType:
                messages.success(request, "No Sales Type was selected for Order Form!  Please try again...")
                return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')

        # Create a unique LeadFileID
        LeadFileID = str(uuid.uuid4())
        LeadFileID = LeadFileID[:25]
            
        # Create new oject of NewOrderInfo model
        order_info = NewOrderInfo.objects.create(
            LeadFileID=LeadFileID,
            Carrier=CarrierName,
            PR_Date=curetime.strftime("%Y-%m-%d"),
            FileName=filename,
            OrderComplete="N",
        )
        order_info.save()
        
        # Store LeadFileID, and FileName in session
        request.session['LeadFileID'] = LeadFileID
        request.session['OrderFileName'] = filename
        
        # Perform new routine to get selective PseudoCID and Sales Type
        if NewOrderForm == "N":
            # Get previous filename and perform create unique LeadFileID and rest of code....
            return render(request, 'DID_OrderForm-1a.html', {})
        
        if selected_option == "New":
            # Get objects from NEW PseudoCID's table and filter by selected Carrier
            pseudo_records = NewPseudoCID.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType, Status="I").order_by('PseudoCID')
            # Get objects from NewClientInfo table
            clients = NewClientInfo.objects.filter(Sales_Type=selected_SalesType)
            return render(request, 'DID_OrderForm-2.html', {'pseudo_records':pseudo_records, 'clients':clients})
        else:
            pseudo_records = ClientList.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')    
                    
            return render(request, 'DID_OrderForm-3.html', {'pseudo_records':pseudo_records})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')

# 
def Create_DIDOrdrForm2a(request):
    if request.user.is_authenticated:
        order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
        CarrierName=order_info.Carrier

        # Get PseudoCID type, Sales Type and Carrier
        selected_option = request.POST.get('pseudoCID_options')
        selected_SalesType = request.POST.get('SalesType_options')
        request.session['SalesType'] = selected_SalesType        
        
        if selected_option == "New":
            # Get objects from NEW PseudoCID's table and filter by selected Carrier
            pseudo_records = NewPseudoCID.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
            # Get objects from NewClientInfo table
            clients = NewClientInfo.objects.filter(Sales_Type=selected_SalesType)
            return render(request, 'DID_OrderForm-2.html', {'pseudo_records':pseudo_records, 'clients':clients})
        else:
            pseudo_records = ClientList.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
            
            return render(request, 'DID_OrderForm-3.html', {'pseudo_records':pseudo_records})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')



# Get amount of DIDs and select PseudoCIDs
def Create_DIDOrdrForm3(request):
    if request.user.is_authenticated:
        # Divide this count by number of 'selected_pseudoCIDs'
        Total_DIDs = request.POST.get('DIDcnt')
        
        # retrieve the relevant NewOrderInfo object using LeadFileID
        order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))

        # Update object with the new value of DID_CNT field
        order_info.Total_DID_CNT = Total_DIDs
        order_info.save()
        
        # create a new object of NewOrderPseudoCID model and associate with the NewOrderInfo object            
        selected_pseudoCIDs = request.POST.getlist('selected_pseudoCIDs[]')
        
        # Validate how many PseudoCIDs were selected
        Tot_Sel_PseudoCIDs = len(selected_pseudoCIDs)
        if Tot_Sel_PseudoCIDs < 1:
            order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
            order_info.delete()
            messages.success(request, "No PseudoCIDs were selected for your Order Form!  Please try again...")
            return redirect('home')
        
        # Get individual DID totals for each PseudoCID selected
        DIDcnts =  int(Total_DIDs) / int(Tot_Sel_PseudoCIDs)
        for value in selected_pseudoCIDs:
            data = value.split(' ', 1)
            pseudoCID=data[0]
            client=data[1]
            clients = NewClientInfo.objects.filter(Client_Description=client, Sales_Type=request.session.get('SalesType'))

            for cinfo in clients:
                NewOrderPseudoCID.objects.create(
                    LeadFileID=order_info.LeadFileID,
                    PseudoCID=pseudoCID,
                    Client_Description=client,
                    Sales_Type=cinfo.Sales_Type,
                    Client_Code=cinfo.Client_Code,
                    PubCode=cinfo.PubCode,
                    InBnd_TranNo=cinfo.InBnd_TranNo,
                    VoiceMail=cinfo.VoiceMail,
                    DID_CNT=DIDcnts,
                    order_info=order_info
                ).save()

        states = States.objects.all()
        return render(request, 'DID_OrderForm-4.html', {'states':states})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


# Select states to order DIDs
def Create_DIDOrdrForm4(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            Total_DIDs = request.POST.get('DIDcnt')
            
            # retrieve the relevant NewOrderInfo object using LeadFileID
            order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))

            # Update object with the new value of DID_CNT field
            order_info.Total_DID_CNT = Total_DIDs
            order_info.save()

            # create a new object of NewOrderPseudoCID model and associate with the NewOrderInfo object            
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCIDs[]')
            selected_clients = request.POST.getlist('selected_clients[]')
                        
            # Validate how many PseudoCIDs and Clients were selected
            Tot_Sel_PseudoCIDs = len(selected_pseudoCIDs)
            Tot_Sel_Clients = len(selected_clients)
            if Tot_Sel_PseudoCIDs < 1:
                order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
                order_info.delete()
                messages.success(request, "No PseudoCIDs were selected for your Order Form!  Please try again...")
                return redirect('home')

            if Tot_Sel_Clients < 1:
                order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
                order_info.delete()
                messages.success(request, "No Clients were selected for your Order Form!  Please try again...")
                return redirect('home')

            # Get individual DID totals for each PseudoCID selected
            DIDcnts =  int(Total_DIDs) / int(Tot_Sel_PseudoCIDs)

            # Cycle through the selected clients
            client_iter = itertools.cycle(selected_clients)
            for idx, pseudo_cid in enumerate(selected_pseudoCIDs):
                client_desc = next(client_iter)
                clients = NewClientInfo.objects.filter(Client_Description=client_desc, Sales_Type=request.session.get('SalesType'))
                for cinfo in clients:
                    NewOrderPseudoCID.objects.create(
                        LeadFileID=order_info.LeadFileID,
                        PseudoCID=pseudo_cid,
                        Client_Description=client_desc,
                        Sales_Type=cinfo.Sales_Type,
                        Client_Code=cinfo.Client_Code,
                        PubCode=cinfo.PubCode,
                        InBnd_TranNo=cinfo.InBnd_TranNo,
                        VoiceMail=cinfo.VoiceMail,
                        DID_CNT=DIDcnts,
                        order_info=order_info
                    ).save()
            
            states = States.objects.all()
            return render(request, 'DID_OrderForm-4.html', {'states':states})
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


def Create_DIDOrdrForm5(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            selected_states = request.POST.getlist('to[]')

            # Validate if States were selected
            if len(selected_states) < 1:
                order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))                
                order_info.delete()
                messages.success(request, "No States were selected for your Order Form!  Please try again...")
                return redirect('home')
            
            # Retrieve the relevant NewOrderInfo & NewOrderPseudoCID objects using LeadFileID
            order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
            order_pseudoCIDs = NewOrderPseudoCID.objects.filter(LeadFileID=order_info.LeadFileID)

            state_string = ",".join(selected_states)            
            order_info.Sel_States = state_string
            order_info.save()
            return render(request, 'DID_OrderForm-5.html', {'order_info':order_info, 'order_pseudoCIDs':order_pseudoCIDs})
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')

#
def DID_OrderForm(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            resp = request.POST.get('action')
            order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))            
            if resp == 'complete':
                return redirect(reverse('DIDOrderForm_Results'))
            elif resp == 'add_to_order':
                order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
                order_info.OrderComplete="N"
                return redirect(reverse('DID_OrderForm-2'))
            elif resp == 'cancel':
                order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
                order_info.delete()
                messages.success(request, "DID Order Form has been Canceled and deleted...")                
            else:
                messages.success(request, "File has been downloaded - Check local PC 'downloads' folder")                
            
            return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


#   
def DIDOrderFrm_Results(request):
    if request.user.is_authenticated:
        data = []

        order_info = NewOrderInfo.objects.filter(FileName=request.session.get('OrderFileName'))
        for OI_record in order_info:
            order_pseudoCIDs = NewOrderPseudoCID.objects.filter(LeadFileID=OI_record.LeadFileID)            
            for pseudoCID in order_pseudoCIDs:
                for x in range(pseudoCID.DID_CNT):
                    state_list = OI_record.Sel_States.split(",")
                    state = state_list[x % len(state_list)]
                    data.append({'DID': '', 'State': state, 'PseudoCID': pseudoCID.PseudoCID, 'LeadID': pseudoCID.LeadFileID})
            #  Set Order complete flag to 'N'  --- FOR TESTING ---
            OI_record.OrderComplete="Y"
            OI_record.save()

        df = pd.DataFrame(data)
        # Create a BytesIO object to store the Excel file
        excel_file = BytesIO()

        # Write the Excel data to the BytesIO object
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        
        # New for AD - Set the appropriate response content type and headers for download
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(request.session.get('OrderFileName') + ".xlsx")
        
        # Write the BytesIO object to the response
        response.write(excel_file.getvalue())

        return response        
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')
    

# DELETE THIS FUNCTION!!
def GetDID_OrderFormInfo(request):
    if request.user.is_authenticated:
        #change 'selected_values' to 'selected_states'
        selected_values = request.POST.getlist('to[]')
        
        return render(request, 'getSelState_Counts.html', {'selected_values':selected_values})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


def Load_DID_Order(request):
    if request.user.is_authenticated:
        if request.method == 'POST' and request.FILES['excel_file']:
            # Create PseudoCID "ADD" records file name
            curetime = datetime.now()            
            etime = curetime.strftime("%Y%m%d%S")
            fetime = etime[:8] + "-" + etime[8:]
            filename = "PSF-" + "ADD_" + fetime + ".csv"
            request.session['PseudoAddFileName'] = filename
            try:
                # Load Carrier Excel Order Form into Pandas DataFrame
                excel_file = request.FILES['excel_file']
                df = pd.read_excel(excel_file, usecols=['DID', 'State', 'PseudoCID', 'LeadID'])
                required_columns = set(['DID', 'State', 'PseudoCID', 'LeadID'])
                file_columns = set(df.columns)
                if not required_columns.issubset(file_columns):
                    raise ValueError('Columns do not match')

                # Shuffle the records within each selective group of PseudoCIDs
                grouped_df = df.groupby('PseudoCID')
                mixed_df = pd.DataFrame()
                for group_name, group_df in grouped_df:
                    group_df = group_df.sample(frac=1, random_state=random.randint(0, 100))
                    mixed_df = pd.concat([mixed_df, group_df])
                
                # Retrieve NewOrderInfo by LeadFileID
                LeadF_ID = mixed_df['LeadID'].unique()
                if len(LeadF_ID) > 0:
                    DID_OrderInfo = []
                    for LF_ID in LeadF_ID:
                        # Retrieve NewOrderInfo & NewOrderPseudoCID by LeadFileID
                        NO_Info = NewOrderInfo.objects.filter(LeadFileID=LF_ID)
                        NO_PseudoCIDs = NewOrderPseudoCID.objects.filter(LeadFileID=LF_ID)
                        if len(NO_Info) > 0 and len(NO_PseudoCIDs) > 0:
                            for info in NO_Info:
                                for data in NO_PseudoCIDs:
                                    # Retrieve or create the ClientList instance based on PseudoCID
                                    client_list_instance, created = ClientList.objects.get_or_create(PseudoCID=data.PseudoCID)
                                    if created:
                                        # Set initial values for the newly created ClientList instance
                                        client_list_instance.Client_Description = data.Client_Description
                                        client_list_instance.Client_Code = data.Client_Code
                                        client_list_instance.PubCode = data.PubCode
                                        client_list_instance.Sales_Type = data.Sales_Type
                                        client_list_instance.VoiceMail = data.VoiceMail
                                        client_list_instance.InBnd_TranNo = data.InBnd_TranNo
                                        client_list_instance.Carrier = info.Carrier
                                        client_list_instance.Status = 'Pending'
                                        client_list_instance.PR_Date = info.PR_Date
                                        client_list_instance.LastUse_Date = None
                                        client_list_instance.DID_CNT = 0  # Initialize DID_CNT to 0
                                        client_list_instance.Notes = ''
                                        client_list_instance.save()

                                        DID_OrderInfo.append({
                                            'PseudoCID': data.PseudoCID,
                                            'Client_Description': data.Client_Description,
                                            'Sales_Type': data.Sales_Type,
                                            'Sel_States': info.Sel_States,
                                            'Carrier': info.Carrier,
                                            # 7/11/23 NEED TO TEST UPDATED DID COUNTS. DELETE ONCE DONE!
                                            #'Tot_DIDs': info.Total_DID_CNT
                                            'Tot_DIDs': data.DID_CNT
                                        })
                                        
                                        # Retrieve records from DataFrame on matching PseudoCID's, 
                                        # then add records to `ClientListData` and `PseudoFile` models
                                        mixed_df['PseudoCID'] = mixed_df['PseudoCID'].astype(str)
                                        df_matching_PseudoCID = mixed_df.loc[mixed_df['PseudoCID'].str.strip() == data.PseudoCID]
                                        # Use transaction.atomic() to ensure data integrity
                                        with transaction.atomic():
                                            # Create an empty list
                                            client_list_data_instances = []

                                        for idx, row in df_matching_PseudoCID.iterrows():
                                            # Fetch the corresponding ClientList instance based on PseudoCID
                                            client_list_instance, created = ClientList.objects.get_or_create(PseudoCID=row['PseudoCID'])
                                            
                                            # Add records to ClientListData model with ForeignKey reference to ClientList instance
                                            client_list_data_instance = ClientListData.objects.create(
                                                PseudoCID=client_list_instance,
                                                PhoneNo=row['DID'],
                                                PhnNo_Loc=row['State'],
                                                Status='Pending',
                                                LeadFileID=row['LeadID'],
                                                Deact_Date=None
                                            )
                                            client_list_data_instances.append(client_list_data_instance)
                                            client_list_instance.update_did_cnt()  # Update DID_CNT for the ClientList instance                                     
                                            
                                            # Add records to `PseudoFile` model
                                            PseudoFile.objects.create(
                                                PseudoCID=row['PseudoCID'],
                                                PhoneNo=row['DID'],
                                                PhnNo_Loc=row['State'],
                                                Client_Code=data.Client_Code,
                                                InBnd_TranNo=data.InBnd_TranNo,
                                                Action="ADD",
                                                LeadFileID=row['LeadID'],
                                                FileName=filename,
                                                Carrier=info.Carrier, 
                                                Deact_Date=None,
                                                OkToArchive="N"
                                            ).save()

                        else:
                            messages.error(request, 'New Order Form Info NOT found for this Order...')
                            return redirect('home')
                else:
                    messages.error(request, 'No LeadFile ID data found in carrier order form')
                    return redirect('home')
                
                # Create process on creating PseudoCID file to upload to Randy's website
                return render(request, 'Create_AddPseudoFile.html', {'DID_OrderInfo':DID_OrderInfo})
            
            except Exception as e: 
                messages.error(request, f'Error while uploading data: {str(e)}')                
                return redirect('home')
        
        elif request.method == 'GET':
            return render(request, 'Load_DIDOrder.html')
        
        else:
            messages.error(request, "Invalid request method or ERROR uploading Excel File.")
            return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')


# Create PseudoCID ADD/Delete files to upload to Randy's website
def Create_Add_PseudoFile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # use this for testing Archive process rather than `curetime` or use 30 days back from current date
            # Make sure to update other lines of code that use `curetime` with `purgedate`
            #purgedate = datetime(2023, 5, 30)
            curetime = datetime.now()            
            PseudoAdd_FileName = request.session.get('PseudoAddFileName')
            # Create a response object with appropriate CSV headers
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{PseudoAdd_FileName}"'
            
            # Create CSV writer using the response object
            writer = csv.writer(response)

            # Write the headers to the CSV file
            writer.writerow(['pseudocid', 'cidnumber', 'cname', 'trixnumber', 'action'])

            PseudoFile_info = PseudoFile.objects.filter(FileName=PseudoAdd_FileName)
            PseudoFile_PseudoCIDs = PseudoFile_info.values('PseudoCID').distinct()
            PseudoFile_info.update(Deact_Date = curetime.strftime("%Y-%m-%d"))
            PseudoFile_info.update(OkToArchive = "Y")

            # Write records to PseudoCID csv file
            for record in PseudoFile_info:
                writer.writerow([record.PseudoCID, record.PhoneNo, record.Client_Code, record.InBnd_TranNo, record.Action])                

            # Archive PseudoFile Records older than 30 days
            PseudoFile_Archive = PseudoFile.objects.filter(Deact_Date__lt=datetime.now() - timedelta(days=30), OkToArchive="Y")
            if PseudoFile_Archive.exists():
                PseudoFile_Archive.delete()
                
            # Set records to "ACTIVE" in `NewPseudoCID`, `ClientList` and `ClientListData` models
            for pseudo_record in PseudoFile_PseudoCIDs:
                pseudo_cid = pseudo_record['PseudoCID']
                # Set records to "Active" in `NewPseudoCID`
                record_update = NewPseudoCID.objects.filter(PseudoCID=pseudo_cid)
                if record_update.exists():
                    record_update.update(Status='A')
                
                # Set records from "Pending" to "Active" in `ClientList` & `ClientListData` models
                ClientList.objects.filter(PseudoCID=pseudo_cid).update(Status='Active')
                ClientListData.objects.filter(PseudoCID=pseudo_cid).update(Status='Active')                
 
            messages.success(request, "PseudoCID 'ADD' File has been created & downloaded - Check local PC 'downloads' folder")            
            return response
        else:
            messages.error(request, "Invalid request method.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')

#
def delete_pseudoCID(request):
    if request.user.is_authenticated:
        records = ClientList.objects.all().order_by('PseudoCID')
        return render(request, 'delete_pseudoCID.html', {'records':records})
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')

#
def delete_results(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCID[]')

            # Validate how many PseudoCIDs were selected
            Tot_Sel_PseudoCIDs = len(selected_pseudoCIDs)
            if(Tot_Sel_PseudoCIDs < 1):
                messages.success(request, "No PseudoCIDs were selected!!  Please try again...")
                return redirect('home')

            client_pseudoCIDs = []
            for value in selected_pseudoCIDs:
                data = value.split(' ', 1)
                pseudoCID=data[0]
                client_pseudoCIDs.extend(ClientList.objects.filter(PseudoCID=pseudoCID))

            return render(request, 'Delete_Results.html', {'client_pseudoCIDs':client_pseudoCIDs})
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')

#
def delete_confirm(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCID')

            if selected_pseudoCIDs:
                # Create PseudoCID "DELETE" records file name
                curetime = datetime.now()
                etime = curetime.strftime("%Y%m%d%S")
                fetime = etime[:8] + "-" + etime[8:]
                
                pseudo_files_to_create = []
                client_list_instances = []

                for pseudoCID in selected_pseudoCIDs:
                    try:
                        client_list_instance = ClientList.objects.get(PseudoCID=pseudoCID)
                        client_list_instance.Status = 'In-Active'
                        client_list_instance.save()
                        client_list_instances.append(client_list_instance)
                        
                        client_list_data_instances = ClientListData.objects.filter(PseudoCID__PseudoCID=pseudoCID)
                        client_list_data_instances.update(Status='In-Active')

                        for client_list_data_instance in client_list_data_instances:
                            pseudo_files_to_create.append(PseudoFile(
                                PseudoCID=client_list_data_instance.PseudoCID.PseudoCID,
                                PhoneNo=client_list_data_instance.PhoneNo,
                                PhnNo_Loc=client_list_data_instance.PhnNo_Loc,
                                Client_Code=client_list_instance.Client_Code,
                                InBnd_TranNo=client_list_instance.InBnd_TranNo,
                                Action='DELETE',
                                LeadFileID=client_list_data_instance.LeadFileID,
                                Carrier=client_list_instance.Carrier,
                                Deact_Date=datetime.now().date(),
                                OkToArchive='NO'
                            ))

                    except ClientList.DoesNotExist:
                        messages.error(request, f"ClientList instance with PseudoCID {pseudoCID} does not exist.")
                        return redirect('home')

                PseudoFile.objects.bulk_create(pseudo_files_to_create)
                                
                context = {
                    'client_list_instances': client_list_instances,
                }

                return render(request, 'Delete_Confirm.html', context)
            else:
                messages.success(request, "No PseudoCIDs were returned...")
                return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


# Create PseudoCID "Delete file" to upload to Randy's website
def Create_Del_PseudoFile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # Create PseudoCID Delete file name
            curetime = datetime.now()            
            etime = curetime.strftime("%Y%m%d%S")
            fetime = etime[:8] + "-" + etime[8:]
            
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCID')
            if selected_pseudoCIDs:
                PseudoFile_info = []
                # Update records in `PseudoFile` for ready to Archive
                for pseudoCID in selected_pseudoCIDs:
                    PSFilename = "PSF-"
                    PseudoFile_info_queryset = PseudoFile.objects.filter(
                        PseudoCID=pseudoCID, 
                        Action='DELETE',
                        Deact_Date=datetime.now().date()
                        )
                    PseudoFile_info_queryset.update(OkToArchive = 'Y')
                    action = PseudoFile_info_queryset.values_list('Action', flat=True).first()                
                    PSFilename = PSFilename + action[:3] + "_" + fetime + ".csv"
                    zipfilename = action + "_Files_" + fetime + ".zip"
                    PseudoFile_info_queryset.update(FileName = PSFilename)
                    PseudoFile_info.extend(PseudoFile_info_queryset)
                
                # Create File Name for PseudoCID csv File
                data = PseudoFile_info[0]
                PseudoCIDFileName = data.FileName
                
                # Create File Name for Carrier Cancelation Excel File
                CancelationFileName = data.Carrier
                CancelationFileName = CancelationFileName + " Canceled DIDs - " + fetime + ".xlsx"

                # Extract the required fields for PseudoCID csv File
                pseudo_records = [
                    [record.PseudoCID, record.PhoneNo, record.Client_Code, record.InBnd_TranNo, record.Action]
                    for record in PseudoFile_info
                ]

                # Create a response object with appropriate CSV headers
                response1 = HttpResponse(content_type='text/csv')
                response1['Content-Disposition'] = 'attachment; filename="{PseudoCIDFileName}"'
                
                # Write the DataFrame to the CSV file
                writer1 = csv.writer(response1)
                writer1.writerow(['pseudocid', 'cidnumber', 'cname', 'trixnumber', 'action'])
                writer1.writerows(pseudo_records)

                # Extract the required fields for Carrier Cancelation Excel File
                cc_records = [
                    [record.PhoneNo, record.PhnNo_Loc]
                    for record in PseudoFile_info
                ]

                # Create a DataFrame from the Carrier Cancelation extracted records for a excel File
                df = pd.DataFrame(cc_records, columns=['DID', 'STATE'])

                # Create Excel file using openpyxl
                wb2 = Workbook()
                ws2 = wb2.active

                # Write the DataFrame to Excel file
                for row in dataframe_to_rows(df, index=False, header=True):
                    ws2.append(row)

                # Save the Excel file in memory
                excel_file = BytesIO()
                wb2.save(excel_file)
                excel_file.seek(0)

                # Create a zip file in memory
                zip_file = BytesIO()
                with ZipFile(zip_file, 'w') as zf:
                    zf.writestr(PseudoCIDFileName, response1.getvalue())
                    zf.writestr(CancelationFileName, excel_file.getvalue())

                # Set the appropriate zip file headers
                response = HttpResponse(zip_file.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zipfilename}"'

                # Delete Records from `ClientList` and `ClientListData` & Update Status in `NewPseudoCID`
                for pseudoCID_Rec in selected_pseudoCIDs:
                    # Retrieve records to delete from ClientList and ClientListData
                    client_list_instances = ClientList.objects.filter(PseudoCID=pseudoCID_Rec)
                    client_list_data_instances = ClientListData.objects.filter(PseudoCID__PseudoCID=pseudoCID_Rec)
                    
                    # Delete records from ClientListData
                    client_list_data_instances.delete()
                    
                    # Delete records from ClientList
                    client_list_instances.delete()

                    # Set records to "INACTIVE" in `NewPseudoCID`
                    record_update = NewPseudoCID.objects.filter(PseudoCID=pseudoCID_Rec)
                    if record_update.exists():
                        record_update.update(Status='I')

                messages.success(request, "Files have been downloaded - Check local PC 'downloads' folder")
                return response # Return single response containing zip file
            else:
                messages.success(request, "No PseudoCIDs were returned...")
                return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


def SearchResults(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            SrchResults = request.POST['SearchInput']
            SrchResults_length = len(SrchResults)
            
            if SrchResults_length != 10:
                messages.success(request, "No results found for that search!.")
                return redirect('home')
            
            SrchData = SrchResults[:6]
            if SrchData == "111111":
                try:  # Search `ClientList` for PseudoCID's
                    client_list = ClientList.objects.get(PseudoCID__contains=SrchResults)
                    client_list_data = ClientListData.objects.filter(PseudoCID=client_list)
                except ClientList.DoesNotExist:
                    messages.success(request, "No results found for that search!.")
                    return redirect('home')
            else:
                try:   # Search `ClientListData` for PhoneNo's
                    client_list_data = ClientListData.objects.get(PhoneNo__contains=SrchResults)
                    # Retrieve `ClientList` record by using ForeignKey relationship
                    client_list = client_list_data.PseudoCID  
                    
                except ClientListData.DoesNotExist:
                    messages.success(request, "No results found for that search!.")
                    return redirect('home')
                    
            context = {
                'client_list_data': client_list_data,
                'client_list': client_list,
            }
            return render(request, 'Search_Results.html', {'context':context})
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


def ResetInActives(request):
    if request.user.is_authenticated:
        # Reset all "In-Active" records to "Active" in ClientList
        updated_records_client_list = ClientList.objects.filter(Status="In-Active").update(Status='Active')

        # Reset all related "In-Active" records to "Active" in ClientListData
        updated_records_client_list_data = ClientListData.objects.filter(PseudoCID__Status="In-Active").update(PseudoCID__Status='Active')

        # Retrieve the updated ClientList records
        client_list_inactive = ClientList.objects.filter(Status="Active")

        #print(record.PseudoCID, record.Status)
        return render(request, 'Reset_InActives.html', {'client_list_inactive': client_list_inactive, 'updated_records_client_list': updated_records_client_list, 'updated_records_client_list_data': updated_records_client_list_data})        
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


# 
def Export_PseudoCID(request):
    if request.user.is_authenticated:
        if request.method == 'POST':        
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCID[]')

            # Validate if PseudoCIDs were selected
            if not selected_pseudoCIDs:
                messages.success(request, "No PseudoCIDs were selected!!  Please try again...")
                return redirect('home')

#            response = PseudoCID_CSV_Download(request, selected_pseudoCIDs)
            # Create response with CSV content
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="export.csv"'
            writer = csv.writer(response)

            # Loop through the selected PseudoCIDs
            for value in selected_pseudoCIDs:
                pseudoCID = value.split(' ', 1)[0]  # Extract the PseudoCID value                

                # Fetch the related ClientList and ClientListData objects in a single query
                #client_list_queryset = ClientList.objects.filter(PseudoCID__in=selected_pseudoCIDs)
                client_list_queryset = ClientList.objects.filter(PseudoCID=pseudoCID)

                for client_list in client_list_queryset:
                    for client_data in client_list.clientlistdata_set.all():
                        writer.writerow([
                            client_list.PseudoCID,
                            client_list.Client_Description,
                            client_list.Client_Code,
                            client_list.PubCode,
                            client_list.Sales_Type,
                            client_data.PhoneNo,
                            client_data.PhnNo_Loc,
                            client_list.VoiceMail,
                            client_list.InBnd_TranNo,
                            client_list.Carrier
                        ])
            
            messages.success(request, "PseudoCID records downloaded to CSV format - Check local PC 'downloads' folder")
            return response
        else:
            # Get all Client Info records
            records = ClientList.objects.all().order_by('PseudoCID')
            return render(request, 'ExportPseudoCID.html', {'records':records})
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

def ImportCSV_ClientInfo(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\ClientInfo.csv"
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert 'None' to None for date fields
                pr_date = datetime.strptime(row['PR_Date'], '%Y-%m-%d') if row['PR_Date'] != 'None' else None
                last_use_date = datetime.strptime(row['LastUse_Date'], '%Y-%m-%d') if row['LastUse_Date'] != 'None' else None
                
                client_info = ClientInfo(
                    PseudoCID=row["PseudoCID"],
                    Client_Description=row["Client_Description"],
                    Client_Code=row["Client_Code"],
                    PubCode=row["PubCode"],
                    Sales_Type=row["Sales_Type"],
                    VoiceMail=row["VoiceMail"],
                    InBnd_TranNo=row["InBnd_TranNo"],
                    Carrier=row["Carrier"],
                    Status=row["Status"],
                    PR_Date= pr_date,
                    LastUse_Date=last_use_date,
                    DID_CNT=row["DID_CNT"],
                    LeadFileID=row["LeadFileID"],
                    Notes=row["Notes"],
                )
                # Save the object to the database
                client_info.save()
            
        messages.success(request, "Imported CSV to Client Info model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

def ImportCSV_CientPseudoCID(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\ClientPseudoCID.csv"
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert 'None' to None for date fields
                deact_date = datetime.strptime(row['Deact_Date'], '%Y-%m-%d') if row['Deact_Date'] != 'None' else None
                
                Client_PseudoCID = ClientPseudoCID(
                    PseudoCID=row["PseudoCID"],
                    PhoneNo=row["PhoneNo"],
                    PhnNo_Loc=row["PhnNo_Loc"],
                    Status=row["Status"],
                    LeadFileID=row["LeadFileID"],                    
                    Deact_Date= deact_date,                    
                )
                # Save the object to the database
                Client_PseudoCID.save()
            
        
        messages.success(request, "Imported CSV to ClientPseudoCID model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

# Functions for importing data to "NEW" models
def ImportCSV_ClientList(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\ClientList.csv"
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert 'None' to None for date fields
                pr_date = datetime.strptime(row['PR_Date'], '%Y-%m-%d') if row['PR_Date'] != 'None' else None
                last_use_date = datetime.strptime(row['LastUse_Date'], '%Y-%m-%d') if row['LastUse_Date'] != 'None' else None

                # Check if a ClientList instance with the PseudoCID already exists
                try:
                    client_list_instance = ClientList.objects.get(PseudoCID=row["PseudoCID"])
                    print("Found ClientList instance:", client_list_instance)
                except ClientList.DoesNotExist:
                    print("ClientList instance not found. Creating a new one...")
                    client_list_instance = ClientList.objects.create(PseudoCID=row["PseudoCID"])
                    print("New ClientList instance created:", client_list_instance)

                # Update the attributes of the existing or newly created ClientList instance
                client_list_instance.Client_Description = row["Client_Description"]
                client_list_instance.Client_Code = row["Client_Code"]
                client_list_instance.PubCode = row["PubCode"]
                client_list_instance.Sales_Type = row["Sales_Type"]
                client_list_instance.VoiceMail = row["VoiceMail"]
                client_list_instance.InBnd_TranNo = row["InBnd_TranNo"]
                client_list_instance.Carrier = row["Carrier"]
                client_list_instance.Status = row["Status"]
                client_list_instance.PR_Date = pr_date
                client_list_instance.LastUse_Date = last_use_date
                client_list_instance.DID_CNT = row["DID_CNT"]
                client_list_instance.Notes = row["Notes"]
                
                # Save the object to the database
                client_list_instance.save()

        messages.success(request, "Imported CSV data to ClientList model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

def ImportCSV_ClientListData(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\ClientListData.csv"
        # Dictionary to store assigned PseudoCID's
        pseudo_cid_dict = {}  
        client_list_data_instances = []
                
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Compare PseudoCID's
                pseudoCID = row["PseudoCID"]
                # If PseudoCID encountered for the first time, assign a unique New LeadFileID
                if pseudoCID not in pseudo_cid_dict:
                    pseudo_cid_dict[pseudoCID] = str(uuid.uuid4())[:25]
                
                # Assign LeadFileID a unique LeadFileID
                if row['LeadFileID'] == 'NA':
                    lead_file_ID = pseudo_cid_dict[pseudoCID]
                else:
                    lead_file_ID = row['LeadFileID']
                
                # Convert 'None' to None for date fields
                deact_date = datetime.strptime(row['Deact_Date'], '%Y-%m-%d') if row['Deact_Date'] != 'None' else None

                # Fetch the corresponding ClientList instance based on pseudoCID
                client_list_instance, created = ClientList.objects.get_or_create(PseudoCID=pseudoCID)                

                # Append the ClientListData instance to the list for bulk_create                
                client_list_data_instance = ClientListData(
                    PseudoCID=client_list_instance,
                    PhoneNo=row["PhoneNo"],
                    PhnNo_Loc=row["PhnNo_Loc"],
                    Status=row["Status"],
                    LeadFileID = lead_file_ID,
                    Deact_Date= deact_date,                    
                )
                client_list_data_instances.append(client_list_data_instance)
                
        # Use transaction.atomic() to ensure data integrity
        with transaction.atomic():
            # Bulk create the ClientListData instances to reduce database hits
            ClientListData.objects.bulk_create(client_list_data_instances)

        # After bulk_create, update the DID_CNT field for each ClientList instance
        for pseudo_cid, instance in pseudo_cid_dict.items():
            client_list_instance = ClientList.objects.get(PseudoCID=pseudo_cid)
            client_list_instance.update_did_cnt()

        messages.success(request, "Imported CSV data to ClientListData model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

# # Test function used to review and test `form`. Remove once testing complete
# def addnew(request):
#     if request.user.is_authenticated:
#         if request.method == "POST":
#             formset = NewOrderInfoForm(request.POST)
#             if formset.is_valid():
#                 formset.save()
#                 messages.success(request, "Data has been saved to database.")
#                 return redirect('home')
            
#         else:
#             formset = NewOrderInfoForm()            

#         return render(request, 'addnew.html', {'formset':formset})
#     else:
#         messages.success(request, "Must be logged in...")
#         return redirect('home')
