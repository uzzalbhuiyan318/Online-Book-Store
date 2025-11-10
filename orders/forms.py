from django import forms
from .models import Order
from accounts.models import Address


class CheckoutForm(forms.Form):
    """Checkout Form"""
    
    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
        required=False
    )
    
    # New address fields
    full_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('cod', 'Cash on Delivery'),
            ('bkash', 'bKash'),
            ('nagad', 'Nagad'),
            ('rocket', 'Rocket'),
            ('sslcommerz', 'Card Payment (SSLCommerz)'),
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    customer_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['address'].queryset = Address.objects.filter(user=user)


class OrderTrackingForm(forms.Form):
    """Order Tracking Form"""
    
    order_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Order Number'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone Number'})
    )
