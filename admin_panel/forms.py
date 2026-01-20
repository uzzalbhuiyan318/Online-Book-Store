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


class CategoryForm(forms.ModelForm):
    """Form for creating/editing categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'name_bn', 'description', 'image', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'name_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name in Bangla'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class OrderStatusForm(forms.ModelForm):
    """Form for updating order status"""
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Status change notes'})
    )
    
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CouponForm(forms.ModelForm):
    """Form for creating/editing coupons"""
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_type', 'discount_value',
            'max_discount_amount', 'min_purchase_amount', 'max_uses',
            'max_uses_per_user', 'valid_from', 'valid_to', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'COUPON CODE', 'style': 'text-transform: uppercase;'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_purchase_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_uses_per_user': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            return code.upper()
        return code
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        if valid_from and valid_to:
            if valid_to <= valid_from:
                raise forms.ValidationError("End date must be after start date.")
        
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        
        if discount_type == 'percentage' and discount_value:
            if discount_value > 100:
                raise forms.ValidationError("Percentage discount cannot exceed 100%.")
            if discount_value <= 0:
                raise forms.ValidationError("Discount value must be greater than 0.")
        
        return cleaned_data


class RentalPlanForm(forms.ModelForm):
    """Form for creating/editing rental plans with book assignment"""
    
    class Meta:
        model = RentalPlan
        fields = [
            'name', 'name_bn', 'description', 'description_bn', 
            'days', 'books', 'price_percentage', 'is_active', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Plan name (English)',
                'required': True
            }),
            'name_bn': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'পরিকল্পনার নাম (বাংলা)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Plan description (English)'
            }),
            'description_bn': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'পরিকল্পনার বিবরণ (বাংলা)'
            }),
            'days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'id': 'id_days'
            }),
            'price_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'readonly': True,
                'style': 'background-color: #f8f9fa;'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'days': 'Number of days for this rental plan',
            'books': 'Select books available for this rental plan',
            'price_percentage': '⚠️ DEPRECATED: This field is no longer used. Rental price is calculated as: ৳10 + (৳2 × days)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from books.models import Book
        
        # Only show active books for selection
        self.fields['books'].queryset = Book.objects.filter(is_active=True).select_related('category').order_by('title')
        
        # Custom widget to add data attributes
        self.fields['books'].widget = forms.SelectMultiple(attrs={
            'class': 'form-control',
            'id': 'id_books',
            'style': 'display: none;'  # Hidden, will be replaced by checkboxes
        })
        
        # Make price_percentage not required since it's deprecated
        self.fields['price_percentage'].required = False
        
        # Add calculated price info to days field
        if self.instance and self.instance.pk:
            calculated_price = self.instance.calculate_rental_price()
            self.fields['days'].help_text = f'Current rental price: ৳{calculated_price} (৳10 + ৳2 × {self.instance.days} days)'
    
    def label_from_instance(self, obj):
        """Custom label for book options with data attributes"""
        return f"{obj.title} - {obj.author}"


class RentalStatusForm(forms.ModelForm):
    """Form for updating rental status"""
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Status change notes'})
    )
    
    class Meta:
        model = BookRental
        fields = ['status', 'payment_status', 'late_fee', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'late_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RentalSettingsForm(forms.ModelForm):
    """Form for rental settings"""
    
    class Meta:
        model = RentalSettings
        fields = [
            'base_rental_fee', 'per_day_rental_fee', 
            'security_deposit_amount', 'daily_late_fee',
            'max_active_rentals_per_user', 'max_renewals',
            'min_stock_for_rental', 'enable_notifications', 'due_soon_days'
        ]
        widgets = {
            'base_rental_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'per_day_rental_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'security_deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'daily_late_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_active_rentals_per_user': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_renewals': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_stock_for_rental': forms.NumberInput(attrs={'class': 'form-control'}),
            'enable_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'due_soon_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BannerForm(forms.ModelForm):
    """Form for creating/editing banners"""
    
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'image', 'link', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Banner title'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Banner subtitle'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Banner link URL'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SupportAgentForm(forms.ModelForm):
    """Form for creating/editing support agents"""
    grant_staff_access = forms.BooleanField(
        required=False,
        initial=True,
        label='Grant Staff Access',
        help_text='Allow this user to access Agent Dashboard (automatically grants is_staff permission)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = SupportAgent
        fields = ['user', 'display_name', 'display_name_bn', 'email', 'avatar', 'bio', 'bio_bn', 'is_online', 'is_active', 'order']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name_bn': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bio_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        
        # Show only users who don't already have a SupportAgent profile
        existing_agent_users = SupportAgent.objects.values_list('user_id', flat=True)
        
        # If editing, include the current agent's user
        if self.instance.pk:
            self.fields['user'].queryset = User.objects.filter(
                Q(id=self.instance.user_id) | ~Q(id__in=existing_agent_users)
            ).order_by('email')
            # Set the current staff status
            self.fields['grant_staff_access'].initial = self.instance.user.is_staff
            # Show user info as text when editing
            self.fields['user'].widget.attrs['readonly'] = True
            self.fields['user'].help_text = f"Current user: {self.instance.user.email}"
        else:
            self.fields['user'].queryset = User.objects.exclude(
                id__in=existing_agent_users
            ).order_by('email')
            self.fields['user'].help_text = "Select a user to assign as support agent"
    
    def save(self, commit=True):
        agent = super().save(commit=False)
        
        # Handle staff access based on checkbox
        grant_staff = self.cleaned_data.get('grant_staff_access', True)
        if agent.user:
            agent.user.is_staff = grant_staff
            agent.user.save()
        
        if commit:
            agent.save()
        return agent


class QuickReplyForm(forms.ModelForm):
    """Form for creating/editing quick replies"""
    
    class Meta:
        model = QuickReply
        fields = ['title', 'title_bn', 'content', 'content_bn', 'category', 'is_active', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'title_bn': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'content_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ChatSettingsForm(forms.ModelForm):
    """Form for chat settings"""
    
    class Meta:
        model = ChatSettings
        fields = [
            'is_enabled', 'widget_position', 'primary_color', 'show_online_status',
            'welcome_message', 'welcome_message_bn', 'offline_message', 'offline_message_bn',
            'auto_assign', 'max_file_size', 'business_hours_start', 'business_hours_end'
        ]
        widgets = {
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'widget_position': forms.Select(attrs={'class': 'form-select'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'show_online_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'welcome_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'welcome_message_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'offline_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'offline_message_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'auto_assign': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_file_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'business_hours_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'business_hours_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class UserAdminForm(forms.ModelForm):
    """Form for creating/editing users in admin"""
    
    class Meta:
        model = User
        fields = ['email', 'phone', 'full_name', 'profile_image', 'is_active', 'is_staff']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReviewApprovalForm(forms.ModelForm):
    """Form for approving/rejecting reviews"""
    
    class Meta:
        model = Review
        fields = ['is_approved']
        widgets = {
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
