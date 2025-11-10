from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import User, Address


class UserRegistrationForm(UserCreationForm):
    """User Registration Form"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    
    class Meta:
        model = User
        fields = ['email', 'phone', 'full_name', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone


class UserLoginForm(AuthenticationForm):
    """User Login Form"""
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class UserProfileForm(forms.ModelForm):
    """User Profile Update Form"""
    
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'profile_image']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AddressForm(forms.ModelForm):
    """Address Form"""
    
    STATE_CHOICES = [
        ('', 'Select Division'),
        ('Dhaka', 'Dhaka'),
        ('Chittagong', 'Chittagong'),
        ('Rajshahi', 'Rajshahi'),
        ('Khulna', 'Khulna'),
        ('Barisal', 'Barisal'),
        ('Sylhet', 'Sylhet'),
        ('Rangpur', 'Rangpur'),
        ('Mymensingh', 'Mymensingh'),
    ]
    
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address (Optional)'})
    )
    
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone', 'email', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House/Flat number, Street name'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Landmark, Area (Optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'Bangladesh'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom Password Change Form"""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Old Password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'})
    )
