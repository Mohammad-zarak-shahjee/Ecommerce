from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('S','Stripe'),
    ('P','Paypal'),
    ('C','Cash-On-Delivery'),
    ('D','Debitcard'),
)
class CheckoutForm(forms.Form):
    #widget is django"s representation of an Html input element
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '90ft Main St',
        'class': 'form-control' 
    }))
    house_address  = forms.CharField(required=False , widget=forms.TextInput(attrs={
        'placeholder': 'House No. 1234',
        'class': 'form-control'
    }))
    #formfiled functions gives the various countries option to select from
    country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class':'custom-select d-block w-100'
    }))
    zip = forms.CharField(widget=forms.TextInput(attrs={
        "class":"form-control"
    }))
    same_shipping_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(widget=forms.RadioSelect,choices=PAYMENT_CHOICES)



class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class' :'form-control',
        'placeholder':'Promo code',
        'aria-label':'Recipient \'s username',
        'aria-describedby':'basic-addon2',
    }))

    # \ is used for special charracters in dictionary data type

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message =forms.CharField(widget= forms.Textarea(attrs={
        'row':3

    }))
    email =forms.EmailField()

