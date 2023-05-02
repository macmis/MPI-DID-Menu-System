from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, F
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .forms import SignUpForm, AddPseudoCIDForm, NewOrderInfoForm, NewOrderPseudoCIDForm
from datetime import datetime
from .models import PhoneRecord, States, Carrier, ClientInfo, ClientPseudoCID, PseudoFile, NewOrderInfo, NewOrderPseudoCID, NewPseudoCID, NewClientInfo
import uuid, itertools
import pandas as pd

# Create your views here.
def home(request):
    # Get list of Client Info and udpate DID counts for each Client
    client_info_list = ClientInfo.objects.all()
    
    for client_info in client_info_list:
        client_info.update_did_cnt()

     # Get selected filter
    sort_option = request.GET.get('sort')

    # Check if sort option was selected
    if sort_option:
        if sort_option == 'sort_by_carrier':
            client_info_list = client_info_list.order_by('Carrier')
        elif sort_option == 'sort_by_pseudoCID':
            client_info_list = client_info_list.order_by('PseudoCID')
        elif sort_option == 'sort_by_prdate':
            client_info_list = client_info_list.order_by('PR_Date')
            
    records = client_info_list.values('PseudoCID', 'Client_Description', 'Sales_Type', 'Carrier', 'Status', 'PR_Date', 'DID_CNT')
    
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
            messages.success(request, "Login Unsuccessful, Please Try Again...")
            return redirect('home')
    else:   
        return render(request, 'home.html', {'records':records})


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
        client_pseudocids = ClientPseudoCID.objects.filter(PseudoCID=pseudo)
        client_info = ClientInfo.objects.filter(PseudoCID=pseudo).first()
        context = {
            'client_pseudocids' : client_pseudocids,
            'client_info' : client_info,
        }
        return render(request, 'pseudoCID.html', {'context':context})
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')


def delete_pseudoCID(request):
    if request.user.is_authenticated:
        records = ClientInfo.objects.all().order_by('PseudoCID')
        return render(request, 'delete_pseudoCID.html', {'records':records})
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')


def delete_results(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            selected_pseudoCIDs = request.POST.getlist('selected_pseudoCIDs')
            #print(selected_pseudoCIDs)
            #if selected_pseudoCIDs:
            #    client_pseudocids = ClientPseudoCID.objects.filter(PseudoCID=selected_pseudoCIDs)
            #    client_info = ClientInfo.objects.filter(PseudoCID=selected_pseudoCIDs).first()
            #    context = {
            #        'client_pseudocids' : client_pseudocids,
            #        'client_info' : client_info,
            #    }
            #    return render(request, 'Delete_Results.html', {'context':context})
            #else:
            #    messages.success(request, "No PseudoCID was selected...")
            #    return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "You Must Be Logged In To View Records...")
        return redirect('home')


def delete_confirm(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            selected_pseudoCID = request.POST.get('selected_pseudoCID')
            if selected_pseudoCID:
                client_pseudocids = ClientPseudoCID.objects.filter(PseudoCID=selected_pseudoCID)
                client_info = ClientInfo.objects.filter(PseudoCID=selected_pseudoCID).first()
                context = {
                    'client_pseudocids' : client_pseudocids,
                    'client_info' : client_info,
                }
                #for record in Del_PseudoResults:
                #    PseudoFile.objects.create(
                #        PseudoCID=record.PseudoCID,
                #        PhoneNo=record.PhoneNo,
                #        ClientCode=record.ClientCode
                #        
                #    )
                return render(request, 'Delete_Confirm.html', {'context':context})
            else:
                messages.success(request, "No PseudoCID was selected...")
                return redirect('home')
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')

    
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
        
        # Store LeadFileID and FileName in session
        request.session['LeadFileID'] = LeadFileID
        request.session['OrderFileName'] = filename
        
        # Perform new routine to get selective PseudoCID and Sales Type
        if NewOrderForm == "N":
            # Get previous filename and perform create unique LeadFileID and rest of code....
            return render(request, 'DID_OrderForm-1a.html', {})
        
        if selected_option == "New":
            # Get objects from NEW PseudoCID's table and filter by selected Carrier
            pseudo_records = NewPseudoCID.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
            # Get objects from NewClientInfo table
            clients = NewClientInfo.objects.filter(Sales_Type=selected_SalesType)
            return render(request, 'DID_OrderForm-2.html', {'pseudo_records':pseudo_records, 'clients':clients})
        else:
            pseudo_records = ClientInfo.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
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
        
        if selected_option == "New":
            # Get objects from NEW PseudoCID's table and filter by selected Carrier
            pseudo_records = NewPseudoCID.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
            # Get objects from NewClientInfo table
            clients = NewClientInfo.objects.filter(Sales_Type=selected_SalesType)
            return render(request, 'DID_OrderForm-2.html', {'pseudo_records':pseudo_records, 'clients':clients})
        else:
            pseudo_records = ClientInfo.objects.filter(Carrier=CarrierName, Sales_Type=selected_SalesType).order_by('PseudoCID')
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
            NewOrderPseudoCID.objects.create(
                LeadFileID=order_info.LeadFileID,
                PseudoCID=data[0],
                Client_Description=data[1],
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
            # Divide this count by number of 'selected_pseudoCIDs'
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
                
                NewOrderPseudoCID.objects.create(
                    LeadFileID=order_info.LeadFileID,
                    PseudoCID=pseudo_cid,
                    Client_Description=client_desc,
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
            else:
                order_info = NewOrderInfo.objects.get(LeadFileID=request.session.get('LeadFileID'))
                order_info.delete()        
                messages.success(request, "DID Order Form has been Canceled and deleted...")
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
        FilePath="C:\Python Development Working Folder\\New Order Forms\\"        

        # Retrieve the relevant NewOrderInfo & NewOrderPseudoCID objects using New Order Info File Name & LeadFileID
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
        df.to_excel(FilePath + request.session.get('OrderFileName') + ".xlsx", index=False)

        #  Perform a process to remove PseudoCID's from `NewPseudoCID` and add record(s) to `ClientInfo`

        OrderFormFile=FilePath+request.session.get('OrderFileName')+".xlsx"
        return render(request, 'DIDOrderForm_Results.html', {'OrderFormFile':OrderFormFile})
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


def Load_DIDOrder(request):
    if request.user.is_authenticated:
        return render(request, 'Load_DIDOrder.html', {})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


def SearchResults(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            SrchResults = request.POST['SearchInput']
            SrchData = SrchResults[:6]
            SrchResults_length = len(SrchResults)
            if SrchResults_length != 10:
                messages.success(request, "No results found for that search!.")
                return redirect('home')
            elif SrchData == "111111":
                client_info = ClientInfo.objects.filter(PseudoCID__contains=SrchResults).first()
                client_pseudocids = ClientPseudoCID.objects.filter(PseudoCID__contains=SrchResults)
            else:
                client_pseudocids = ClientPseudoCID.objects.filter(PhoneNo__contains=SrchResults)
                client_info = None
                for pseudocid in client_pseudocids:
                    client_info = ClientInfo.objects.filter(PseudoCID__contains=pseudocid.PseudoCID).first()
                    break
                    
            context = {
                'client_pseudocids' : client_pseudocids,
                'client_info' : client_info,
            }
            return render(request, 'Search_Results.html', {'context':context})
        else:
            messages.success(request, "This view only accepts POST request.")
            return redirect('home')
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')


# Test function used to review and test `form`. Remove once testing complete
def addnew(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            formset = NewOrderInfoForm(request.POST)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Data has been saved to database.")
                return redirect('home')
            
        else:
            formset = NewOrderInfoForm()            

        return render(request, 'addnew.html', {'formset':formset})
    else:
        messages.success(request, "Must be logged in...")
        return redirect('home')
