from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import PhoneRecord, NewOrderInfo, NewOrderPseudoCID

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(label="", max_length=50 , widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}))
    last_name = forms.CharField(label="", max_length=50 , widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}))
    email = forms.EmailField(label="", widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email Address'}))
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'User Name'
        self.fields['username'].label = ''
        self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
        self.fields['password2'].label = ''
        self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'	


# Create Add PseudoCID Form
class AddPseudoCIDForm(forms.ModelForm):
    PhoneNo = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Phone Number", "class":"form-control"}), label="")
    PseudoCID = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"PseudoCID", "class":"form-control"}), label="")
    TFN_PrimaryNo = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"YES/NO", "class":"form-control"}), label="")
    DID_Location = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"DID State Location", "class":"form-control"}), label="")
    Sales_Type = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Sales Type", "class":"form-control"}), label="")
    PubCode = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Pub Code", "class":"form-control"}), label="")
    ClientCode = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Client Code", "class":"form-control"}), label="")
    Client_Description = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Client Description", "class":"form-control"}), label="")
    VoiceMail = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Client VM Box", "class":"form-control"}), label="")
    Carrier = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"SIP Carrier", "class":"form-control"}), label="")
    PR_status = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"PR Status=P", "class":"form-control"}), label="")
    PR_Date = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"PR Date", "class":"form-control"}), label="")
    LastUse_Date = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Last Use Date", "class":"form-control"}), label="")
    Notes = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder":"Notes", "class":"form-control"}), label="")

    class Meta:
        model = PhoneRecord
        exclude = ("user",)
        

class NewOrderInfoForm(forms.ModelForm):
    class Meta:
        model = NewOrderInfo
        fields = ['LeadFileID', 'Carrier', 'Total_DID_CNT', 'Sel_States', 'PR_Date', 'FileName']
        widgets = {
            'PR_Date': forms.DateInput(attrs={'type': 'date'})
        }


class NewOrderPseudoCIDForm(forms.ModelForm):
    class Meta:
        model = NewOrderPseudoCID
        fields = ['LeadFileID', 'PseudoCID', 'Client_Description']
