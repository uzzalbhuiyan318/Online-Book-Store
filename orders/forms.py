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

    gift_address = forms.ModelChoiceField(
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

    # Gift fields
    is_gift = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'is_gift_checkbox'})
    )
    gift_from_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sender name'})
    )
    gift_from_alt_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alternative Phone No'})
    )
    gift_from_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sender phone'})
    )
    gift_message = forms.CharField(
        max_length=120,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'gift_message', 'maxlength': '120', 'placeholder': 'Write a short message (max 120 characters)'}),
        required=False
    )
    gift_deliver_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    # Gift recipient fields (to whom the gift is sent)
    gift_to_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient name'})
    )
    gift_to_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient phone'})
    )
    gift_to_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Recipient email'})
    )
    # Recipient selects
    COUNTRY_CHOICES = [
        ('Bangladesh', 'Bangladesh'),
    ]
    CITY_CHOICES = [
        ('', 'Select City'),
        ('Dhaka', 'Dhaka'),
        ('Chattogram', 'Chattogram'),
        ('Khulna', 'Khulna'),
        ('Rajshahi', 'Rajshahi'),
        ('Barishal', 'Barishal'),
        ('Rangpur', 'Rangpur'),
        ('Mymensingh', 'Mymensingh'),
        ('Sylhet', 'Sylhet'),
    ]
    AREA_CHOICES = [
        ('', 'Select Area'),
        ('Gulshan', 'Gulshan'),
        ('Banani', 'Banani'),
        ('Dhanmondi', 'Dhanmondi'),
        ('Motijheel', 'Motijheel'),
        ('Mirpur', 'Mirpur'),
    ]

    ZONE_CHOICES = [
        ('', 'Select Zone'),
        ('North', 'North'),
        ('South', 'South'),
        ('East', 'East'),
        ('West', 'West'),
        ('Central', 'Central'),
    ]

    gift_to_country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gift_to_city = forms.ChoiceField(
        choices=[('', 'Select City')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Area and Zone are populated dynamically by JavaScript, so we use IntegerField
    # to avoid validation errors when choices aren't pre-populated
    gift_to_area = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gift_to_zone = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gift_to_address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address line 1'})
    )
    gift_to_address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address line 2'})
    )
    gift_to_state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Division'})
    )
    gift_to_postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'})
    )
    gift_to_occasion = forms.ChoiceField(
        choices=[('', 'Select Occasion')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['address'].queryset = Address.objects.filter(user=user)
            self.fields['gift_address'].queryset = Address.objects.filter(user=user)
        
        # Populate city dropdown from database
        from .models import GiftCity, GiftOccasion
        cities = GiftCity.objects.all().order_by('name')
        city_choices = [('', 'Select City')] + [(str(city.id), city.name) for city in cities]
        self.fields['gift_to_city'].choices = city_choices
        
        # Populate occasion dropdown from database
        occasions = GiftOccasion.objects.all().order_by('label')
        occasion_choices = [('', 'Select Occasion')] + [(occasion.key, occasion.label) for occasion in occasions]
        self.fields['gift_to_occasion'].choices = occasion_choices
        
        # Note: gift_to_area and gift_to_zone are IntegerFields
        # They accept any integer value and are populated dynamically via JavaScript


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
