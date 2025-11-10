from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm,
    AddressForm, CustomPasswordChangeForm
)
from .models import Address
from orders.models import Order
from books.models import Wishlist


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('books:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to BookStore.')
            return redirect('books:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('books:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.full_name}!')
                next_url = request.GET.get('next', 'books:home')
                return redirect(next_url)
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('books:home')


@login_required
def profile(request):
    """User profile view"""
    # Handle profile update
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Handle profile information update
            user = request.user
            user.full_name = request.POST.get('full_name', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            
            # Handle profile image upload
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
            
            try:
                user.save()
                messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
            
            return redirect('accounts:profile')
        
        elif form_type == 'password':
            # Handle password change
            form = CustomPasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('accounts:profile')
            else:
                # Add form errors to messages
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
                return redirect('accounts:profile')
    
    # GET request - display profile
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    addresses = Address.objects.filter(user=request.user)
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('book')[:6]
    
    context = {
        'recent_orders': orders,
        'addresses': addresses,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def address_list(request):
    """List all addresses"""
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def add_address(request):
    """Add new address"""
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is the first address, make it default
            if not addresses.exists():
                address.is_default = True
            
            # If setting as default, remove default from others
            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('accounts:address_list')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/address_form.html', {
        'form': form, 
        'action': 'Add',
        'addresses': addresses
    })


@login_required
def edit_address(request, pk):
    """Edit existing address"""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            
            # If setting as default, remove default from others
            if updated_address.is_default:
                Address.objects.filter(user=request.user).exclude(pk=pk).update(is_default=False)
            
            updated_address.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'accounts/address_form.html', {
        'form': form, 
        'action': 'Edit',
        'address': address,
        'addresses': addresses
    })


@login_required
def delete_address(request, pk):
    """Delete address"""
    from django.http import JsonResponse
    
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        
        # If this was the default address, set another as default
        if address.is_default:
            first_address = Address.objects.filter(user=request.user).first()
            if first_address:
                first_address.is_default = True
                first_address.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Address deleted successfully!'})
        
        messages.success(request, 'Address deleted successfully!')
        return redirect('accounts:address_list')
    
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})


@login_required
def set_default_address(request, pk):
    """Set address as default"""
    from django.http import JsonResponse
    
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Remove default from all addresses
        Address.objects.filter(user=request.user).update(is_default=False)
        
        # Set this address as default
        address.is_default = True
        address.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Default address updated!'})
        
        messages.success(request, 'Default address updated!')
        return redirect('accounts:address_list')
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
