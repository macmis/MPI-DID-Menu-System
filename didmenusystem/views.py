from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import F, Case, When, Value, CharField, Count
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotAllowed, FileResponse
from django.core import serializers
from .forms import SignUpForm, LastUseDateEditForm, AddPseudoCIDForm, NewOrderInfoForm, NewOrderPseudoCIDForm
from datetime import datetime, timedelta
from .models import States, Carrier, ClientList, ClientListData, NewOrderList, NewOrderListData, MPIPseudoCIDs, MPIClients, PseudoFile, ClientInfo, ClientPseudoCID, NewOrderInfo, NewOrderPseudoCID, NewPseudoCID, NewClientInfo, PhoneRecord
from io import BytesIO
from zipfile import ZipFile
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import uuid, itertools, csv, random, json
from itertools import zip_longest
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
            # Carrier1 = TouchTone, Carrier2 = CCI
            carrier1 = carrier_info_list[0] if len(carrier_info_list) >= 1 else None
            carrier2 = carrier_info_list[1] if len(carrier_info_list) >= 2 else None
            
            # Perform filters by user selection
            if sort_option == "split_by_carrier_All":
                client_info_list1 = ClientList.objects.filter(Carrier=carrier1.CarrierName).order_by('Client_Description')
                client_info_list2 = ClientList.objects.filter(Carrier=carrier2.CarrierName).order_by('Client_Description')
            elif sort_option == "split_by_carrier_Res":
                client_info_list1 = ClientList.objects.filter(Carrier=carrier1.CarrierName, Sales_Type="R").order_by('Client_Description')
                client_info_list2 = ClientList.objects.filter(Carrier=carrier2.CarrierName, Sales_Type="R").order_by('Client_Description')
            elif sort_option == "split_by_carrier_Bus":
                client_info_list1 = ClientList.objects.filter(Carrier=carrier1.CarrierName, Sales_Type="B").order_by('Client_Description')
                client_info_list2 = ClientList.objects.filter(Carrier=carrier2.CarrierName, Sales_Type="B").order_by('Client_Description')
                
            records_carrier1 = client_info_list1.values('PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier')
            records_carrier2 = client_info_list2.values('PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier')

            # Create seperate QuerySet for Serialize JSON
            records_json_carrier1 = client_info_list1.values('PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier')
            records_json_carrier2 = client_info_list2.values('PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier')

            # Convert date fields to string format for Export_CSV function
            for record in records_json_carrier1:
                record['LastUse_Date'] = record['LastUse_Date'].strftime('%Y-%m-%d') if record['LastUse_Date'] else None
                record['PR_Date'] = record['PR_Date'].strftime('%Y-%m-%d')

            for record in records_json_carrier2:
                record['LastUse_Date'] = record['LastUse_Date'].strftime('%Y-%m-%d') if record['LastUse_Date'] else None
                record['PR_Date'] = record['PR_Date'].strftime('%Y-%m-%d')
                        
            records = None
            # Combine the two lists of records into pairs using zip_longest
            combined_records = zip_longest(records_carrier1, records_carrier2)
            json_combined_records = zip_longest(records_json_carrier1, records_json_carrier2)            
            combined_records_json = json.dumps(list(json_combined_records))

            # Pass the combined_records list to the template
            return render(request, 'home.html', {'combined_records': combined_records, 'combined_records_json': combined_records_json, 'carrier1': carrier1, 'carrier2': carrier2, 'filter_selection': filter_selection})
            
        else:
            filter_selection = sort_option
            if filter_selection == 'sort_by_carrier_All':
                client_info_list = client_info_list.order_by('Carrier', 'Sales_Type', 'Client_Description')
            elif filter_selection == 'sort_by_carrier_Res':
                client_info_list = client_info_list.filter(Sales_Type="R").order_by('Carrier', 'Client_Description')
            elif filter_selection == 'sort_by_carrier_Bus':
                client_info_list = client_info_list.filter(Sales_Type="B").order_by('Carrier', 'Client_Description')
            elif filter_selection == 'sort_by_pseudoCID':
                client_info_list = client_info_list.order_by('PseudoCID')
            elif filter_selection == 'sort_by_udate':
                client_info_list = client_info_list.order_by('-LastUse_Date')
            elif filter_selection == 'sort_by_prdate':
                client_info_list = client_info_list.order_by('PR_Date')

            records = client_info_list.values('PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status', 'LastUse_Date', 'PR_Date', 'DID_CNT')
            
            # Create seperate QuerySet for Serialize JSON
            records_csv = client_info_list.values('PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status', 'LastUse_Date', 'PR_Date', 'DID_CNT')

            # Convert date fields to string format for Export_CSV function
            for record in records_csv:
                record['LastUse_Date'] = record['LastUse_Date'].strftime('%Y-%m-%d') if record['LastUse_Date'] else None
                record['PR_Date'] = record['PR_Date'].strftime('%Y-%m-%d')

            # Serialize the QuerySet - `records_json` used for Export_CSV function
            records_json = json.dumps(list(records_csv))
            
            records_carrier1 = None
            records_carrier2 = None
            carrier1 = None
            carrier2 = None
    else:
        # First, order by Carrier, then sort Sales_Type with preference for 'R'
        client_info_list = client_info_list.annotate(
            sales_type_order=Case(
                When(Sales_Type='R', then=Value(1)),
                When(Sales_Type='B', then=Value(2)),
                default=Value(3),
                output_field=CharField(),
            )
        ).order_by('sales_type_order', 'Carrier', 'Client_Description')
        
        records = client_info_list.values(
            'PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status',
            'LastUse_Date', 'PR_Date', 'DID_CNT'
        )

        # Create seperate QuerySet for Serialize JSON
        records_csv = client_info_list.values(
            'PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status',
            'LastUse_Date', 'PR_Date', 'DID_CNT'
        )
        
        # Convert date fields to string format for Export_CSV function
        for record in records_csv:
            record['LastUse_Date'] = record['LastUse_Date'].strftime('%Y-%m-%d') if record['LastUse_Date'] else None
            record['PR_Date'] = record['PR_Date'].strftime('%Y-%m-%d')

        # Serialize the QuerySet - `records_json` used for Export_CSV function
        records_json = json.dumps(list(records_csv))

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
        return render(request, 'home.html', {'records':records, 'records_json':records_json, 'carrier1':carrier1, 'carrier2':carrier2, 'records_carrier1':records_carrier1, 'records_carrier2':records_carrier2, 'filter_selection': filter_selection})


# Function to handle form submission for editing `LastUse_Date`
def edit_lastuse_date(request, pseudo_cid):
    client = get_object_or_404(ClientList, PseudoCID=pseudo_cid)    

    if request.method == 'POST':
        edit_form = LastUseDateEditForm(request.POST, instance=client)        
        if edit_form.is_valid():
            edit_form.save()

            messages.success(request, f"Date Usage for {client.PseudoCID} has been updated.")
            return redirect('home')  # Redirect back to the home page or another appropriate view
    else:
        edit_form = LastUseDateEditForm(instance=client)

    return render(request, 'edit_lastuse_date.html', {'client': client, 'edit_form': edit_form})


# Function to handle logout procedure
def logout_user(request):
    logout(request)
    messages.success(request, "You Have Successfully Logged Out...")
    return redirect('home')

# Function to handle registering a new user
# Temporary commented out. Review ways to activate at administrator level
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


# Function to handle hyper-link home page for `PseudoCID`
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
        order_info_incomplete = NewOrderList.objects.filter(OrderComplete="N")

        # Delete incomplete records
        order_info_incomplete.delete()

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
    
    
# Get amount of DIDs, select non-active PseudoCIDs and assign to MPI list of Clients
def Create_DIDOrdrForm2(request):
    if request.user.is_authenticated:
        curetime = datetime.now()
        NewOrderForm="Y" # Flag to identify a NEW order form. 

        # Continuation from Existing order form
        if request.method == 'GET':
            order_list = NewOrderList.objects.get(LeadFileID=request.session.get('LeadFileID'))
            filename=order_list.FileName
            CarrierName=order_list.Carrier
            NewOrderForm=order_list.OrderComplete
        # Create a NEW order form
        elif request.method == 'POST': 
            # Get PseudoCID type, Sales Type and Carrier
            selected_option = request.POST.get('pseudoCID_options')
            selected_SalesType = request.POST.get('SalesType_options')
            request.session['SalesType'] = selected_SalesType            
            selected_carrier = request.POST.get('selected_carrier')
            # Create order form file name
            CarrierInfo = selected_carrier.split()
            CarrierName = CarrierInfo[0]
            filename = CarrierInfo[2] + "-Order_"
            etime = curetime.strftime("%Y%m%d%S")
            fetime = etime[:8] + "-" + etime[8:]
            filename = filename + fetime

            # Validate user selected a "Carrier" and "Sales Type"
            if not selected_carrier:
                messages.success(request, "No Carrier was selected for Order Form!  Please try again...")
                return redirect('home')
            
            if not selected_SalesType:
                messages.success(request, "No Sales Type was selected for Order Form!  Please try again...")
                return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')

        # Create a unique LeadFileID for New Order Form
        LeadFileID = str(uuid.uuid4())
        LeadFileID = LeadFileID[:25]
            
        # Create new object of NewOrderList model
        order_list = NewOrderList.objects.create(
            LeadFileID=LeadFileID,
            Carrier=CarrierName,
            Total_DID_CNT=0,
            Sel_States="",
            PR_Date=curetime.strftime("%Y-%m-%d"),
            FileName=filename,
            OrderComplete="N",
        )
        
        # Store LeadFileID, and FileName in session
        request.session['LeadFileID'] = LeadFileID
        request.session['OrderFileName'] = filename
        
        # Perform new routine to get selective PseudoCID and Sales Type
        if NewOrderForm == "N":
            # Get previous filename and perform create unique LeadFileID and rest of code....
            return render(request, 'DID_OrderForm-1a.html', {})
        
        if selected_option == "New":
            # Get objects from MPIPseudoCIDs table and filter by selected Carrier
            pseudo_records = MPIPseudoCIDs.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType, Status="I").order_by('PseudoCID')
            # Get objects from MPIClients table
            clients = MPIClients.objects.filter(Sales_Type=selected_SalesType)
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
        order_list = NewOrderList.objects.get(LeadFileID=request.session.get('LeadFileID'))
        CarrierName=order_list.Carrier

        # Get PseudoCID type, Sales Type and Carrier
        selected_option = request.POST.get('pseudoCID_options')
        selected_SalesType = request.POST.get('SalesType_options')
        request.session['SalesType'] = selected_SalesType        
        
        if selected_option == "New":
            # Get objects from MPIPseudoCIDs table and filter by selected Carrier
            pseudo_records = MPIPseudoCIDs.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
            # Get objects from MPIClients table
            clients = MPIClients.objects.filter(Sales_Type=selected_SalesType)
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
        # Get the number DID's user requested
        Total_DIDs = request.POST.get('DIDcnt')
        
        # retrieve the relevant NewOrderList object using LeadFileID
        order_list = NewOrderList.objects.get(LeadFileID=request.session.get('LeadFileID'))

        # Update object with the new value to DID_CNT field
        order_list.Total_DID_CNT = Total_DIDs
        order_list.save()
        
        # Get list of selected PseudoCIDs
        selected_pseudoCIDs = request.POST.getlist('selected_pseudoCIDs[]')
        
        # Validate how many PseudoCIDs were selected, then delete `NewOrderList` if not valid selection
        Tot_Sel_PseudoCIDs = len(selected_pseudoCIDs)
        if Tot_Sel_PseudoCIDs < 1:
            order_file_name = request.session.get('OrderFileName')
            # Retrieve all NewOrderList instances with the matching OrderFileName
            matching_order_lists = NewOrderList.objects.filter(FileName=order_file_name)

            # Iterate through each matching NewOrderList instance
            for matching_order_list in matching_order_lists:
                # Delete associated NewOrderListData instances
                matching_order_list.pseudo_cids.all().delete()
                                
                # Delete the NewOrderList instance
                matching_order_list.delete()                
            
            messages.success(request, "No PseudoCIDs were selected for your Order Form!  Please try again...")
            return redirect('home')
        
        # Create a list of NewOrderListData instances to be bulk created
        new_order_list_data_instances = []
        
        # Calculate idivdual DID counts for each selected PseudoCID
        DIDcnts =  int(Total_DIDs) / int(Tot_Sel_PseudoCIDs)
        for value in selected_pseudoCIDs:
            data = value.split(' ', 1)
            pseudoCID=data[0]
            client=data[1]
            clients = MPIClients.objects.filter(Client_Description=client, Sales_Type=request.session.get('SalesType'))

            # Create new object of NewOrderListData model and associate with the NewOrderList object            
            for cinfo in clients:
                new_order_list_data_instance = NewOrderListData(
                    LeadFileID=order_list.LeadFileID,
                    PseudoCID=pseudoCID,
                    Client_Description=client,
                    Sales_Type=cinfo.Sales_Type,
                    Client_Code=cinfo.Client_Code,
                    PubCode=cinfo.PubCode,
                    InBnd_TranNo=cinfo.InBnd_TranNo,
                    VoiceMail=cinfo.VoiceMail,
                    DID_CNT=DIDcnts,
                    order_list=order_list,  # Explicitly set the ForeignKey                    
                )
                new_order_list_data_instances.append(new_order_list_data_instance)

        # Explicitly commit the transaction before bulk creating instances
        transaction.commit()
        
        # Use transaction.atomic() to ensure data integrity
        with transaction.atomic():
            NewOrderListData.objects.bulk_create(new_order_list_data_instances)

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
            
            # retrieve the relevant NewOrderList object using LeadFileID
            order_list = NewOrderList.objects.get(LeadFileID=request.session.get('LeadFileID'))
            
            # Update object with the new value of DID_CNT field
            order_list.Total_DID_CNT = Total_DIDs
            order_list.save()

            # create a new object of NewOrderListData model and associate with the NewOrderLis object
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCIDs[]')
            selected_clients = request.POST.getlist('selected_clients[]')
                        
            # Validate how many PseudoCIDs and Clients were selected
            Tot_Sel_PseudoCIDs = len(selected_pseudoCIDs)
            Tot_Sel_Clients = len(selected_clients)
            if Tot_Sel_PseudoCIDs < 1:
                order_file_name = request.session.get('OrderFileName')
                # Retrieve all NewOrderList instances with the matching OrderFileName
                matching_order_lists = NewOrderList.objects.filter(FileName=order_file_name)

                # Iterate through each matching NewOrderList instance
                for matching_order_list in matching_order_lists:
                    # Delete associated NewOrderListData instances
                    matching_order_list.pseudo_cids.all().delete()
                                    
                    # Delete the NewOrderList instance
                    matching_order_list.delete()                
                
                messages.success(request, "No PseudoCIDs were selected for your Order Form!  Please try again...")
                return redirect('home')

            if Tot_Sel_Clients < 1:
                order_file_name = request.session.get('OrderFileName')
                # Retrieve all NewOrderList instances with the matching OrderFileName
                matching_order_lists = NewOrderList.objects.filter(FileName=order_file_name)

                # Iterate through each matching NewOrderList instance
                for matching_order_list in matching_order_lists:
                    # Delete associated NewOrderListData instances
                    matching_order_list.pseudo_cids.all().delete()
                                    
                    # Delete the NewOrderList instance
                    matching_order_list.delete()                
                
                messages.success(request, "No Clients were selected for your Order Form!  Please try again...")
                return redirect('home')

            # Get individual DID counts for each selected PseudoCID
            DIDcnts =  int(Total_DIDs) / int(Tot_Sel_PseudoCIDs)

            # Create a list of NewOrderListData instances to be bulk created
            new_order_list_data_instances = []
            
            # Cycle through the selected clients
            client_iter = itertools.cycle(selected_clients)
            for idx, pseudo_cid in enumerate(selected_pseudoCIDs):
                client_desc = next(client_iter)
                clients = MPIClients.objects.filter(Client_Description=client_desc, Sales_Type=request.session.get('SalesType'))
                for cinfo in clients:
                    new_order_list_data_instance = NewOrderListData(
                        LeadFileID=order_list.LeadFileID,
                        PseudoCID=pseudo_cid,
                        Client_Description=client_desc,
                        Sales_Type=cinfo.Sales_Type,
                        Client_Code=cinfo.Client_Code,
                        PubCode=cinfo.PubCode,
                        InBnd_TranNo=cinfo.InBnd_TranNo,
                        VoiceMail=cinfo.VoiceMail,
                        DID_CNT=DIDcnts,
                        order_list=order_list,  # Explicitly set the ForeignKey
                    )
                    new_order_list_data_instances.append(new_order_list_data_instance)
            
            # Explicitly commit the transaction before bulk creating instances
            transaction.commit()

            # Use transaction.atomic() to ensure data integrity
            with transaction.atomic():
                NewOrderListData.objects.bulk_create(new_order_list_data_instances)

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
                order_file_name = request.session.get('OrderFileName')
                # Retrieve all NewOrderList instances with the matching OrderFileName
                matching_order_lists = NewOrderList.objects.filter(FileName=order_file_name)

                # Iterate through each matching NewOrderList instance
                for matching_order_list in matching_order_lists:
                    # Delete associated NewOrderListData instances
                    matching_order_list.pseudo_cids.all().delete()
                                    
                    # Delete the NewOrderList instance
                    matching_order_list.delete()                
                
                messages.success(request, "No States were selected for your Order Form!  Please try again...")
                return redirect('home')
            
            # Retrieve the relevant NewOrderList object using LeadFileID
            order_list_leadfile = NewOrderList.objects.filter(LeadFileID=request.session.get('LeadFileID'))

            state_string = ",".join(selected_states)                
            for order_list in order_list_leadfile:
                order_list.Sel_States = state_string
                order_list.save()

            # Retrieve related NewOrderListData instances using the related name 'FileName'
            order_list_data = NewOrderListData.objects.filter(order_list__FileName=request.session.get('OrderFileName'))

            return render(request, 'DID_OrderForm-5.html', {'order_list_data': order_list_data})
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
            order_list = NewOrderList.objects.get(LeadFileID=request.session.get('LeadFileID'))            
            if resp == 'complete':
                return redirect(reverse('DIDOrderForm_Results'))
            elif resp == 'add_to_order':
                order_list.OrderComplete = "N"
                order_list.save()
                return redirect(reverse('DID_OrderForm-2'))
            elif resp == 'cancel':
                order_file_name = request.session.get('OrderFileName')
                # Retrieve all NewOrderList instances with the matching OrderFileName
                matching_order_lists = NewOrderList.objects.filter(FileName=order_file_name)
                
                # Iterate through each matching NewOrderList instance
                for matching_order_list in matching_order_lists:
                    # Delete associated NewOrderListData instances
                    matching_order_list.pseudo_cids.all().delete()
                    
                    # Delete the NewOrderList instance
                    matching_order_list.delete()
                
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
        order_list = NewOrderList.objects.filter(FileName=request.session.get('OrderFileName'))
        for OI_record in order_list:
            order_list_data = NewOrderListData.objects.filter(order_list__LeadFileID=OI_record.LeadFileID)
            for pseudoCID in order_list_data:
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


#
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
                
                # Retrieve NewOrderList by LeadFileID
                LeadF_ID = mixed_df['LeadID'].unique()
                if len(LeadF_ID) > 0:
                    DID_OrderInfo = []
                    for LF_ID in LeadF_ID:
                        # Retrieve NewOrderList & NewOrderListData by LeadFileID
                        order_list = NewOrderList.objects.filter(LeadFileID=LF_ID)
                        order_list_data = NewOrderListData.objects.filter(order_list__LeadFileID=LF_ID)
                        if len(order_list) > 0 and len(order_list_data) > 0:
                            for info in order_list:
                                for data in order_list_data:
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
                                            'Tot_DIDs': data.DID_CNT
                                        })
                                        
                                        # Retrieve records from DataFrame on matching PseudoCID's, 
                                        # then add records to `ClientListData` and `PseudoFile` models
                                        mixed_df['PseudoCID'] = mixed_df['PseudoCID'].astype(str)
                                        df_matching_PseudoCID = mixed_df.loc[mixed_df['PseudoCID'].str.strip() == data.PseudoCID]
                                        
                                        # Use transaction.atomic() to ensure data integrity & create empty list
                                        with transaction.atomic():
                                            client_list_data_instances = []

                                        # Fetch the corresponding ClientList instance based on PseudoCID
                                        for idx, row in df_matching_PseudoCID.iterrows():
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
                                            # Update DID_CNT for the ClientList instance
                                            client_list_instance.update_did_cnt()  
                                            
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


# Create PseudoCID "ADD" file to upload to Randy's website
def Create_Add_PseudoFile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # use this for testing Archive process rather than `curetime` or use 30 days back from current date
            # Make sure to update other lines of code that use `curetime` with `purgedate`
            # purgedate = datetime(2023, 5, 30)
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
                
            # Set records to "ACTIVE" in `MPIPseudoCIDs`, `ClientList` and `ClientListData` models
            for pseudo_record in PseudoFile_PseudoCIDs:
                pseudo_cid = pseudo_record['PseudoCID']
                # Set records to "Active" in `MPIPseudoCIDs`
                record_update = MPIPseudoCIDs.objects.filter(PseudoCID=pseudo_cid)
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

# Display list of MPI Client names with PseudoCIDs to select for deletion
def delete_pseudoCID(request):
    if request.user.is_authenticated:
        records = ClientList.objects.all().order_by('PseudoCID')
        return render(request, 'delete_pseudoCID.html', {'records':records})
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')


# Display list of selected Client names with PseudoCIDs to confirm deletion
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


# Create PseudoCID "Delete" file to upload to Randy's website
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

                # Delete Records from `ClientList`, `ClientListData` & Update Status in `MPIPseudoCIDs`
                for pseudoCID_Rec in selected_pseudoCIDs:
                    # Retrieve records to delete from ClientList and ClientListData
                    client_list_instances = ClientList.objects.filter(PseudoCID=pseudoCID_Rec)
                    client_list_data_instances = ClientListData.objects.filter(PseudoCID__PseudoCID=pseudoCID_Rec)
                    
                    # Delete records from ClientListData
                    client_list_data_instances.delete()
                    
                    # Delete records from ClientList
                    client_list_instances.delete()

                    # Set records to "INACTIVE" in `MPIPseudoCIDs`
                    record_update = MPIPseudoCIDs.objects.filter(PseudoCID=pseudoCID_Rec)
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


# 
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

# 
def Export_PseudoCID(request):
    if request.user.is_authenticated:
        if request.method == 'POST':        
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCID[]')

            # Validate if PseudoCIDs were selected
            if not selected_pseudoCIDs:
                messages.success(request, "No PseudoCIDs were selected!!  Please try again...")
                return redirect('home')

            # Create PseudoCID Export File Name
            curetime = datetime.now()
            etime = curetime.strftime("%H%M%S")
            Pseudo_ExpFile = "PseudoCID_File-" + etime + ".csv"
            
            # Create response with CSV content
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{Pseudo_ExpFile}"'
            writer = csv.writer(response)

            writer.writerow([
                'PseudoCID', 'Client_Description', 'Client_Code', 'PubCode', 'Sales_Type', 'PhoneNo', 'PhnNo_Loc', 'VoiceMail', 'InBnd_TranNo', 'Carrier'
            ])
                
            # Loop through the selected PseudoCIDs
            for value in selected_pseudoCIDs:
                pseudoCID = value.split(' ', 1)[0]  # Extract the PseudoCID value                

                # Fetch the related ClientList and ClientListData objects in a single query
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


# Export home screen records to CSV format
def Export_CSV(request):
    if request.user.is_authenticated:
        records_json = request.POST.get('records_json')
        combined_records_json = request.POST.get('combined_records_json')

        # Create Home Screen CSV file name
        curetime = datetime.now()
        etime = curetime.strftime("%H%M%S")
        CSV_fileName = "HomeScreen-" + etime + ".csv"

        # Create response with CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{CSV_fileName}"'
        writer = csv.writer(response)
        
        if records_json:
            writer.writerow([
                'PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier'
            ])
            
            try:
                records_list = json.loads(records_json)

                # Get JSON records
                for record in records_list:
                    pseudo_cid = record.get('PseudoCID', '')
                    client_description = record.get('Client_Description', '')
                    sales_type = record.get('Sales_Type', '')
                    last_use_date = record.get('LastUse_Date', '')
                    pr_date = record.get('PR_Date', '')
                    did_count = record.get('DID_CNT', '')
                    carrier = record.get('Carrier', '')

                    writer.writerow([
                        pseudo_cid,
                        client_description,
                        sales_type,
                        last_use_date,
                        pr_date,
                        did_count,
                        carrier   
                    ])

            except json.JSONDecodeError as e:
                print("JSON decoding error:", e)

        elif combined_records_json:
            writer.writerow([
                'PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier',
                'PseudoCID', 'Client_Description', 'Sales_Type', 'LastUse_Date', 'PR_Date', 'DID_CNT', 'Carrier'
            ])
            
            try:
                combined_records_list = json.loads(combined_records_json)

                # Get JSON combined records
                for record_pair in combined_records_list:
                    record_C1, record_C2 = record_pair

                    pseudo_cid_C1 = record_C1.get('PseudoCID', '') if record_C1 else ''
                    client_description_C1 = record_C1.get('Client_Description', '') if record_C1 else ''
                    sales_type_C1 = record_C1.get('Sales_Type', '') if record_C1 else ''
                    last_use_date_C1 = record_C1.get('LastUse_Date', '') if record_C1 else ''
                    pr_date_C1 = record_C1.get('PR_Date', '') if record_C1 else ''
                    did_count_C1 = record_C1.get('DID_CNT', '') if record_C1 else ''
                    carrier_C1 = record_C1.get('Carrier', '') if record_C1 else ''
                    
                    pseudo_cid_C2 = record_C2.get('PseudoCID', '') if record_C2 else ''
                    client_description_C2 = record_C2.get('Client_Description', '') if record_C2 else ''
                    sales_type_C2 = record_C2.get('Sales_Type', '') if record_C2 else ''
                    last_use_date_C2 = record_C2.get('LastUse_Date', '') if record_C2 else ''
                    pr_date_C2 = record_C2.get('PR_Date', '') if record_C2 else ''
                    did_count_C2 = record_C2.get('DID_CNT', '') if record_C2 else ''
                    carrier_C2 = record_C2.get('Carrier', '') if record_C2 else ''

                    writer.writerow([
                        pseudo_cid_C1,
                        client_description_C1,
                        sales_type_C1,
                        last_use_date_C1,
                        pr_date_C1,
                        did_count_C1,
                        carrier_C1,
                        pseudo_cid_C2,
                        client_description_C2,
                        sales_type_C2,
                        last_use_date_C2,
                        pr_date_C2,
                        did_count_C2,
                        carrier_C2
                    ])
                    
            except json.JSONDecodeError as e:
                print("JSON decoding error:", e)
            

        messages.success(request, "Exported Home Screen Results to CSV format - Check local PC 'downloads' folder")
        #return redirect('home')
        return response
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

#
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

#
def ImportCSV_NewOrderList(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\NewOrderList.csv"
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert 'None' to None for date fields
                pr_date = datetime.strptime(row['PR_Date'], '%Y-%m-%d') if row['PR_Date'] != 'None' else None

                # Check if a NewOrderList instance with the LeadFileID already exists
                try:
                    neworder_list_instance = NewOrderList.objects.get(LeadFileID=row["LeadFileID"])
                    print("Found NewOrderList instance:", neworder_list_instance)
                except NewOrderList.DoesNotExist:
                    print("NewOrderList instance not found. Creating a new one...")
                    neworder_list_instance = NewOrderList.objects.create(LeadFileID=row["LeadFileID"])
                    print("New NewOrderList instance created:", neworder_list_instance)

                # Update the attributes of the existing or newly created NewOrderList instance
                neworder_list_instance.Carrier = row["Carrier"]
                neworder_list_instance.Total_DID_CNT = row["Total_DID_CNT"]
                neworder_list_instance.Sel_States = row["Sel_States"]
                neworder_list_instance.PR_Date = pr_date
                neworder_list_instance.FileName = row["FileName"]
                neworder_list_instance.OrderComplete = row["OrderComplete"]
                
                # Save the object to the database
                neworder_list_instance.save()

        messages.success(request, "Imported CSV data to NewOrderList model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')


#
def ImportCSV_NewOrderListData(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\NewOrderListData.csv"
                
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Compare LeadFileIDs
                leadfileID = row["LeadFileID"]

                # Fetch the corresponding NewOrderList instance based on LeadFileID
                neworder_list_instance, created = NewOrderList.objects.get_or_create(LeadFileID=leadfileID)                

                # Create NewOrderListData instance and associate with the NewOrderList instance
                neworder_list_data_instance = NewOrderListData(
                    order_list=neworder_list_instance,  # Associate with the NewOrderList instance
                    PseudoCID=row["PseudoCID"],
                    Client_Description=row["Client_Description"],
                    Sales_Type=row["Sales_Type"],
                    Client_Code = row["Client_Code"],
                    PubCode = row["PubCode"],
                    InBnd_TranNo = row["InBnd_TranNo"],
                    VoiceMail = row["VoiceMail"],
                    DID_CNT = row["DID_CNT"],
                )
                
                # Save the NewOrderListData instance to the database
                neworder_list_data_instance.save()
                
        messages.success(request, "Imported CSV data to NewOrderListData model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

#
def ImportCSV_MPIPseudoCIDs(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\MPIPseudoCIDs.csv"
        
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                
                MPI_PseudoCIDs = MPIPseudoCIDs(
                    PseudoCID=row["PseudoCID"],
                    Sales_Type=row["Sales_Type"],
                    Carrier=row["Carrier"],
                    Status=row["Status"],
                )
                # Save the object to the database
                MPI_PseudoCIDs.save()
                
        messages.success(request, "Imported CSV data to MPIPseudoCIDs model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')


#
def ImportCSV_MPIClients(request):
    if request.user.is_authenticated:
        file_path = "C:\Python Development\\MPIClients.csv"
        
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                
                MPI_Clients = MPIClients(
                    Client_Description=row["Client_Description"],
                    Sales_Type=row["Sales_Type"],
                    Client_Code=row["Client_Code"],
                    PubCode=row["PubCode"],
                    InBnd_TranNo=row["InBnd_TranNo"],
                    VoiceMail=row["VoiceMail"],                    
                )
                # Save the object to the database
                MPI_Clients.save()
                
        messages.success(request, "Imported CSV data to MPIClients model...")
        return redirect('home')
    else:
        messages.error(request, "Must be logged in...")
        return redirect('home')

    
    

# This function can be deleted once new model `ClientList` is in production
# Make sure to remove from `admin.py`, `models.py` and import definitions
# def ImportCSV_ClientInfo(request):
#     if request.user.is_authenticated:
#         file_path = "C:\Python Development\\ClientInfo.csv"
#         with open(file_path, newline="") as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Convert 'None' to None for date fields
#                 pr_date = datetime.strptime(row['PR_Date'], '%Y-%m-%d') if row['PR_Date'] != 'None' else None
#                 last_use_date = datetime.strptime(row['LastUse_Date'], '%Y-%m-%d') if row['LastUse_Date'] != 'None' else None
                
#                 client_info = ClientInfo(
#                     PseudoCID=row["PseudoCID"],
#                     Client_Description=row["Client_Description"],
#                     Client_Code=row["Client_Code"],
#                     PubCode=row["PubCode"],
#                     Sales_Type=row["Sales_Type"],
#                     VoiceMail=row["VoiceMail"],
#                     InBnd_TranNo=row["InBnd_TranNo"],
#                     Carrier=row["Carrier"],
#                     Status=row["Status"],
#                     PR_Date= pr_date,
#                     LastUse_Date=last_use_date,
#                     DID_CNT=row["DID_CNT"],
#                     LeadFileID=row["LeadFileID"],
#                     Notes=row["Notes"],
#                 )
#                 # Save the object to the database
#                 client_info.save()
            
#         messages.success(request, "Imported CSV to Client Info model...")
#         return redirect('home')
#     else:
#         messages.error(request, "Must be logged in...")
#         return redirect('home')

# #
# # This function can be deleted once new model `ClientListData` is in production
# # Make sure to remove from `admin.py`, `models.py` and import definitions
# def ImportCSV_CientPseudoCID(request):
#     if request.user.is_authenticated:
#         file_path = "C:\Python Development\\ClientPseudoCID.csv"
#         with open(file_path, newline="") as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Convert 'None' to None for date fields
#                 deact_date = datetime.strptime(row['Deact_Date'], '%Y-%m-%d') if row['Deact_Date'] != 'None' else None
                
#                 Client_PseudoCID = ClientPseudoCID(
#                     PseudoCID=row["PseudoCID"],
#                     PhoneNo=row["PhoneNo"],
#                     PhnNo_Loc=row["PhnNo_Loc"],
#                     Status=row["Status"],
#                     LeadFileID=row["LeadFileID"],                    
#                     Deact_Date= deact_date,                    
#                 )
#                 # Save the object to the database
#                 Client_PseudoCID.save()
            
        
#         messages.success(request, "Imported CSV to ClientPseudoCID model...")
#         return redirect('home')
#     else:
#         messages.error(request, "Must be logged in...")
#         return redirect('home')


# This function may be deleted... Was used for testing. 
# def ResetInActives(request):
#     if request.user.is_authenticated:
#         # Reset all "In-Active" records to "Active" in ClientList
#         updated_records_client_list = ClientList.objects.filter(Status="In-Active").update(Status='Active')

#         # Reset all related "In-Active" records to "Active" in ClientListData
#         updated_records_client_list_data = ClientListData.objects.filter(PseudoCID__Status="In-Active").update(PseudoCID__Status='Active')

#         # Retrieve the updated ClientList records
#         client_list_inactive = ClientList.objects.filter(Status="Active")

#         #print(record.PseudoCID, record.Status)
#         return render(request, 'Reset_InActives.html', {'client_list_inactive': client_list_inactive, 'updated_records_client_list': updated_records_client_list, 'updated_records_client_list_data': updated_records_client_list_data})        
#     else:
#         messages.success(request, "Must be logged in...")
#         return redirect('home')



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
