from django import forms
from .models import Order, GiftCity, GiftArea, GiftZone
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
    
    # City/Area/Zone dropdowns for delivery address
    delivery_city = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_delivery_city'})
    )
    delivery_area = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_delivery_area'})
    )
    delivery_zone = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_delivery_zone'})
    )
    
    # Keep old fields for backward compatibility (hidden)
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput()
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.HiddenInput()
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.HiddenInput()
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
    gift_to_city = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_gift_to_city'})
    )
    gift_to_area = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_gift_to_area'})
    )
    gift_to_zone = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_gift_to_zone'})
    )
    gift_to_address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full address'})
    )
    OCCASION_CHOICES = [
        ('', 'Select Occasion'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('congratulations', 'Congratulations'),
        ('thanks', 'Thanks'),
        ('other', 'Other'),
    ]
    gift_to_occasion = forms.ChoiceField(
        choices=OCCASION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['address'].queryset = Address.objects.filter(user=user)
            self.fields['gift_address'].queryset = Address.objects.filter(user=user)
        
        # Populate delivery_city with all cities from database
        city_choices = [('', 'Select City')]
        cities = GiftCity.objects.all().order_by('name')
        for city in cities:
            city_choices.append((city.id, city.name))
        self.fields['delivery_city'].widget.choices = city_choices
        
        # Populate delivery_area with all areas from database
        area_choices = [('', 'Select Area')]
        areas = GiftArea.objects.all().order_by('name')
        for area in areas:
            area_choices.append((area.id, area.name))
        self.fields['delivery_area'].widget.choices = area_choices
        
        # Populate delivery_zone with all zones from database
        zone_choices = [('', 'Select Zone')]
        zones = GiftZone.objects.all().order_by('name')
        for zone in zones:
            zone_choices.append((zone.id, zone.name))
        self.fields['delivery_zone'].widget.choices = zone_choices
        
        # Populate gift_to_city with all cities from database
        city_choices = [('', 'Select City')]
        cities = GiftCity.objects.all().order_by('name')
        for city in cities:
            city_choices.append((city.id, city.name))
        self.fields['gift_to_city'].widget.choices = city_choices
        
        # Populate gift_to_area with all areas from database
        area_choices = [('', 'Select Area')]
        areas = GiftArea.objects.all().order_by('name')
        for area in areas:
            area_choices.append((area.id, area.name))
        self.fields['gift_to_area'].widget.choices = area_choices
        
        # Populate gift_to_zone with all zones from database
        zone_choices = [('', 'Select Zone')]
        zones = GiftZone.objects.all().order_by('name')
        for zone in zones:
            zone_choices.append((zone.id, zone.name))
        self.fields['gift_to_zone'].widget.choices = zone_choices

    def clean_gift_from_phone(self):
        """Validate gift sender phone number - must be exactly 11 digits"""
        import re
        phone = self.cleaned_data.get('gift_from_phone', '').strip()
        
        # Skip validation if field is empty (it's optional)
        if not phone:
            return phone
        
        # Check if phone number is exactly 11 digits
        if not re.match(r'^\d{11}$', phone):
            raise forms.ValidationError('Phone number must be exactly 11 digits')
        
        return phone
    
    def clean_gift_to_phone(self):
        """Validate gift recipient phone number - must be exactly 11 digits"""
        import re
        phone = self.cleaned_data.get('gift_to_phone', '').strip()
        
        # Skip validation if field is empty (it's optional)
        if not phone:
            return phone
        
        # Check if phone number is exactly 11 digits
        if not re.match(r'^\d{11}$', phone):
            raise forms.ValidationError('Phone number must be exactly 11 digits')
        
        return phone
    
    def clean_gift_from_name(self):
        """Validate gift sender name - must contain only letters and spaces"""
        import re
        name = self.cleaned_data.get('gift_from_name', '').strip()
        
        # Skip validation if field is empty (it's optional)
        if not name:
            return name
        
        # Check if name contains only letters and spaces
        if not re.match(r'^[a-zA-Z\s]+$', name):
            raise forms.ValidationError('Name must contain only letters and spaces')
        
        return name
    
    def clean_gift_to_name(self):
        """Validate gift recipient name - must contain only letters and spaces"""
        import re
        name = self.cleaned_data.get('gift_to_name', '').strip()
        
        # Skip validation if field is empty (it's optional)
        if not name:
            return name
        
        # Check if name contains only letters and spaces
        if not re.match(r'^[a-zA-Z\s]+$', name):
            raise forms.ValidationError('Name must contain only letters and spaces')
        
        return name


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
