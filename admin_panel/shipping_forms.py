from django import forms
from django.db.models import Q
from books.models import Book, Category, Review, Banner
from orders.models import Order, Coupon, ShippingFee
from rentals.models import RentalPlan, BookRental, RentalSettings
from support.models import SupportAgent, QuickReply, ChatSettings
from accounts.models import User


class BookForm(forms.ModelForm):
    """Form for creating/editing books with Bangla support"""
    
    class Meta:
        model = Book
        fields = [
            'title', 'title_bn', 'author', 'author_bn', 'publisher', 'publisher_bn',
            'isbn', 'description', 'description_bn', 'short_description', 'short_description_bn',
            'category', 'language', 'price', 'discount_price', 'stock',
            'cover_image', 'image2', 'image3', 'pages', 'publication_date',
            'edition', 'is_active', 'is_featured', 'is_bestseller'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title (English)'}),
            'title_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title (Bangla)'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name (English)'}),
            'author_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name (Bangla)'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter publisher name (English)'}),
            'publisher_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter publisher name (Bangla)'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ISBN'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Book description in English'}),
            'description_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Book description in Bangla'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description in English'}),
            'short_description_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description in Bangla'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'image2': forms.FileInput(attrs={'class': 'form-control'}),
            'image3': forms.FileInput(attrs={'class': 'form-control'}),
            'pages': forms.NumberInput(attrs={'class': 'form-control'}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'edition': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_bestseller': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ShippingFeeForm(forms.ModelForm):
    """Form for creating/editing shipping fees"""
    
    class Meta:
        model = ShippingFee
        fields = ['city_name', 'city_name_bn', 'fee', 'is_default', 'is_active']
        widgets = {
            'city_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City name in English'}),
            'city_name_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City name in Bangla'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'city_name': 'City name will be matched case-insensitively',
            'fee': 'Shipping fee in BDT (৳)',
            'is_default': 'Mark as default fee for cities not in the list',
        }
    
    def clean_city_name(self):
        city_name = self.cleaned_data.get('city_name')
        if city_name:
            existing = ShippingFee.objects.filter(city_name__iexact=city_name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(f"A shipping fee for '{city_name}' already exists.")
        return city_name
