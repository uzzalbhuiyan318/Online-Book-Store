from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from decimal import Decimal
from .models import Order, OrderItem, OrderStatusHistory
from django.http import JsonResponse
from .models import GiftCity, GiftArea, GiftZone, GiftForm, GiftOccasion
from .forms import CheckoutForm, OrderTrackingForm
from .email_utils import send_order_confirmation_email
from books.models import Cart
from accounts.models import Address
from payments.utils import initiate_payment
import logging

logger = logging.getLogger(__name__)


def calculate_shipping_fee(city):
    """Calculate shipping fee based on city
    
    Args:
        city: City name (string)
        
    Returns:
        Decimal: Shipping fee (0 if no city, database value for city, or default fee)
    """
    from .models import ShippingFee
    from django.core.cache import cache
    
    if not city:
        return Decimal('0.00')  # Return 0 if no city selected
    
    # Normalize city name for comparison (case-insensitive, strip whitespace)
    city_normalized = city.strip().lower()
    
    # Check cache first for performance
    cache_key = f'shipping_fee_{city_normalized}'
    cached_fee = cache.get(cache_key)
    if cached_fee is not None:
        return Decimal(str(cached_fee))
    
    # Query database for city-specific fee
    try:
        shipping_fee = ShippingFee.objects.get(
            city_name__iexact=city,
            is_active=True
        )
        fee = shipping_fee.fee
    except ShippingFee.DoesNotExist:
        # Get default fee for cities not in the list
        default_fee = ShippingFee.objects.filter(
            is_default=True,
            is_active=True
        ).first()
        fee = default_fee.fee if default_fee else Decimal('120.00')  # Fallback if no default set
    
    # Cache for 1 hour (3600 seconds)
    cache.set(cache_key, float(fee), 3600)
    return fee


def checkout(request):
    """Checkout view - Shows cart and handles order placement"""
    # Get cart items for both authenticated and guest users
    cart_items = []
    
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).select_related('book')
    elif request.session.session_key:
        cart_items = Cart.objects.filter(session_key=request.session.session_key).select_related('book')
    
    # Calculate totals
    subtotal = sum(item.subtotal for item in cart_items) if cart_items else 0
    
    # Get addresses if user is authenticated (needed for shipping calculation)
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id') if request.user.is_authenticated else []
    
    # Calculate shipping based on default/first address city
    shipping_city = None
    if request.user.is_authenticated and addresses:
        # Get default address or first address
        default_address = addresses.filter(is_default=True).first() or addresses.first()
        if default_address:
            shipping_city = default_address.city
    
    shipping = calculate_shipping_fee(shipping_city) if subtotal > 0 else Decimal('0.00')
    
    # Get coupon discount from session
    discount = Decimal(str(request.session.get('discount', 0)))
    coupon_code = request.session.get('coupon_code', None)
    
    total = subtotal + shipping - discount
    
    # Handle form submission - REQUIRE LOGIN for order placement
    if request.method == 'POST':
        # Require login to place order
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to complete your order.')
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        
        # Check if cart is empty
        cart_items = Cart.objects.filter(user=request.user).select_related('book')
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('orders:checkout')
        
        # Check stock availability
        for item in cart_items:
            if item.quantity > item.book.stock:
                messages.error(request, f'{item.book.title} has insufficient stock.')
                return redirect('orders:checkout')
        
        # Recalculate totals for order placement
        subtotal = sum(item.subtotal for item in cart_items)
        
        # Determine shipping city from selected/entered address
        shipping_city = None
        is_gift = request.POST.get('is_gift') == 'on'
        
        if is_gift:
            # For gift orders, use recipient city
            # Check if gift address was selected
            gift_address_id = request.POST.get('gift_address')
            if gift_address_id:
                try:
                    gift_address = Address.objects.get(id=gift_address_id, user=request.user)
                    shipping_city = gift_address.city
                except Address.DoesNotExist:
                    pass
            else:
                # Get city from gift recipient form (GiftCity model ID)
                gift_city_id = request.POST.get('gift_to_city')
                if gift_city_id:
                    try:
                        from .models import GiftCity
                        gift_city_obj = GiftCity.objects.get(id=gift_city_id)
                        shipping_city = gift_city_obj.name
                    except (GiftCity.DoesNotExist, ValueError):
                        pass
        else:
            # For normal orders, use delivery address
            address_id = request.POST.get('address_id')
            
            if address_id:
                # Get city from selected address
                try:
                    selected_address = Address.objects.get(id=address_id, user=request.user)
                    shipping_city = selected_address.city
                except Address.DoesNotExist:
                    pass
            else:
                # Get city from new address form
                shipping_city = request.POST.get('city')
        
        shipping = calculate_shipping_fee(shipping_city)
        
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Get or create shipping address
            # If this is a gift order, prefer gift address fields
            if form.cleaned_data.get('is_gift'):
                # Check if user selected an existing address for the gift recipient
                gift_address_id = request.POST.get('gift_address') or request.POST.get('gift_address_id')
                if gift_address_id:
                    gift_address = get_object_or_404(Address, id=gift_address_id, user=request.user)
                    shipping_data = {
                        'shipping_full_name': gift_address.full_name,
                        'shipping_phone': gift_address.phone,
                        'shipping_email': gift_address.email,
                        'shipping_address_line1': gift_address.address_line1,
                        'shipping_address_line2': gift_address.address_line2,
                        'shipping_city': gift_address.city,
                        'shipping_state': gift_address.state,
                        'shipping_postal_code': gift_address.postal_code,
                        'shipping_country': gift_address.country,
                    }
                else:
                    # Use recipient fields submitted as part of gift form
                    shipping_data = {
                        'shipping_full_name': form.cleaned_data.get('gift_to_name') or form.cleaned_data.get('full_name'),
                        'shipping_phone': form.cleaned_data.get('gift_to_phone') or form.cleaned_data.get('phone'),
                        'shipping_email': form.cleaned_data.get('gift_to_email') or form.cleaned_data.get('email'),
                        'shipping_address_line1': form.cleaned_data.get('gift_to_address_line1') or form.cleaned_data.get('address_line1'),
                        'shipping_address_line2': '',
                        'shipping_city': form.cleaned_data.get('gift_to_city') or form.cleaned_data.get('city'),
                        'shipping_state': '',
                        'shipping_postal_code': '',
                        'shipping_country': form.cleaned_data.get('gift_to_country') or 'Bangladesh',
                    }
            else:
                address_id = request.POST.get('address_id')
                
                if address_id:
                    # Use existing address
                    address = get_object_or_404(Address, id=address_id, user=request.user)
                    shipping_data = {
                        'shipping_full_name': address.full_name,
                        'shipping_phone': address.phone,
                        'shipping_email': address.email,
                        'shipping_address_line1': address.address_line1,
                        'shipping_address_line2': address.address_line2,
                        'shipping_city': address.city,
                        'shipping_state': address.state,
                        'shipping_postal_code': address.postal_code,
                        'shipping_country': address.country,
                    }
                else:
                    # Use new address
                    shipping_data = {
                        'shipping_full_name': form.cleaned_data['full_name'],
                        'shipping_phone': form.cleaned_data['phone'],
                        'shipping_email': form.cleaned_data['email'],
                        'shipping_address_line1': form.cleaned_data['address_line1'],
                        'shipping_address_line2': form.cleaned_data['address_line2'],
                        'shipping_city': form.cleaned_data['city'],
                        'shipping_state': form.cleaned_data['state'],
                        'shipping_postal_code': form.cleaned_data['postal_code'],
                        'shipping_country': 'Bangladesh',
                    }
            
            # Get discount from session
            discount = Decimal(str(request.session.get('discount', 0)))
            final_total = subtotal + shipping - discount
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                payment_method=form.cleaned_data['payment_method'],
                subtotal=subtotal,
                shipping_cost=shipping,
                discount=discount,
                total=final_total,
                customer_notes=form.cleaned_data.get('customer_notes', ''),
                # Gift related fields
                is_gift=form.cleaned_data.get('is_gift', False),
                gift_from_name=form.cleaned_data.get('gift_from_name', '') or None,
                gift_from_phone=form.cleaned_data.get('gift_from_phone', '') or None,
                gift_from_alt_phone=form.cleaned_data.get('gift_from_alt_phone', '') or None,
                gift_message=form.cleaned_data.get('gift_message', '') or None,
                gift_occasion=form.cleaned_data.get('gift_to_occasion', '') or None,
                gift_zone=form.cleaned_data.get('gift_to_zone', '') or None,
                gift_deliver_date=form.cleaned_data.get('gift_deliver_date', None),
                **shipping_data
            )

            # If this was a gift order, create a separate GiftForm record for admin handling
            if form.cleaned_data.get('is_gift'):
                try:
                    city_obj = None
                    area_obj = None
                    zone_obj = None
                    occasion_obj = None

                    city_id = form.cleaned_data.get('gift_to_city')
                    area_id = form.cleaned_data.get('gift_to_area')
                    zone_id = form.cleaned_data.get('gift_to_zone')
                    occasion_key = form.cleaned_data.get('gift_to_occasion')

                    if city_id:
                        try:
                            city_obj = GiftCity.objects.get(pk=city_id)
                        except GiftCity.DoesNotExist:
                            city_obj = None
                    if area_id:
                        try:
                            area_obj = GiftArea.objects.get(pk=area_id)
                        except GiftArea.DoesNotExist:
                            area_obj = None
                    if zone_id:
                        try:
                            zone_obj = GiftZone.objects.get(pk=zone_id)
                        except GiftZone.DoesNotExist:
                            zone_obj = None
                    if occasion_key:
                        occasion_obj = GiftOccasion.objects.filter(key=occasion_key).first()

                    GiftForm.objects.create(
                        order=order,
                        is_gift=True,
                        from_name=form.cleaned_data.get('gift_from_name') or None,
                        from_phone=form.cleaned_data.get('gift_from_phone') or None,
                        from_alt_phone=form.cleaned_data.get('gift_from_alt_phone') or None,
                        to_name=form.cleaned_data.get('gift_to_name') or None,
                        to_phone=form.cleaned_data.get('gift_to_phone') or None,
                        to_email=form.cleaned_data.get('gift_to_email') or None,
                        to_address_line1=form.cleaned_data.get('gift_to_address_line1') or None,
                        to_address_line2=None,
                        city=city_obj,
                        area=area_obj,
                        zone=zone_obj,
                        postal_code=None,
                        state=None,
                        occasion=occasion_obj,
                        message=form.cleaned_data.get('gift_message') or None,
                        deliver_date=form.cleaned_data.get('gift_deliver_date') or None,
                    )
                except Exception as e:
                    logger.exception('Failed to create GiftForm record: %s', e)
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    book=item.book,
                    book_title=item.book.title,
                    book_author=item.book.author,
                    book_isbn=item.book.isbn,
                    quantity=item.quantity,
                    price=item.book.final_price,
                    subtotal=item.subtotal
                )
                
                # Update book stock and sales
                item.book.stock -= item.quantity
                item.book.sales += item.quantity
                item.book.save(update_fields=['stock', 'sales'])
            
            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes='Order placed',
                changed_by=request.user
            )
            
            # Record coupon usage if coupon was used
            coupon_id = request.session.get('coupon_id')
            if coupon_id:
                from .models import Coupon, CouponUsage
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    # Create coupon usage record
                    CouponUsage.objects.create(
                        coupon=coupon,
                        user=request.user,
                        order=order
                    )
                    # Increment coupon used count
                    coupon.used_count += 1
                    coupon.save(update_fields=['used_count'])
                    
                    # Clear coupon from session
                    for key in ['coupon_code', 'coupon_id', 'discount']:
                        if key in request.session:
                            del request.session[key]
                except Coupon.DoesNotExist:
                    pass
            
            # Clear cart
            cart_items.delete()
            
            # Handle payment
            payment_method = form.cleaned_data['payment_method']
            
            if payment_method == 'cod':
                # Cash on Delivery - confirm order and send email
                order.status = 'confirmed'
                order.confirmed_at = timezone.now()
                order.save()
                
                logger.info(f"COD order {order.order_number} confirmed, attempting to send email to {order.user.email}")
                
                # Send order confirmation email with invoice
                try:
                    result = send_order_confirmation_email(order)
                    if result:
                        logger.info(f"✅ Order confirmation email sent successfully for COD order {order.order_number}")
                    else:
                        logger.warning(f"⚠️ Email function returned False for order {order.order_number}")
                except Exception as e:  # noqa: broad-except
                    logger.error(f"❌ Failed to send confirmation email for order {order.order_number}: {str(e)}")
                    logger.exception("Full exception traceback:")
                    # Don't fail the order if email fails
                
                messages.success(request, 'Order placed successfully! Check your email for order confirmation.')
                return redirect('orders:order_success', order_number=order.order_number)
            else:
                # Redirect to payment gateway
                payment_url = initiate_payment(order, payment_method)
                if payment_url:
                    return redirect(payment_url)
                else:
                    messages.error(request, 'Payment initialization failed. Please try again.')
                    return redirect('orders:order_detail', order_number=order.order_number)
        else:
            # Form validation failed
            logger.error(f"Checkout form validation failed. Errors: {form.errors.as_json()}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            # Fall through to render the form with errors
    else:
        form = CheckoutForm(user=request.user if request.user.is_authenticated else None)
    
    # Get user addresses only if authenticated
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    else:
        addresses = []
    
    # Prepare context (discount already calculated above)
    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping,
        'discount': discount,
        'coupon_code': coupon_code,
        'total': total,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


def order_success(request, order_number):
    """Order success page - accessible without login for payment callbacks, but re-authenticates user if session lost"""
    logger.info(f"order_success called for order_number: {order_number}, user authenticated: {request.user.is_authenticated}")
    
    # Try to get order - allow access for payment callbacks even if user is not logged in
    try:
        if request.user.is_authenticated:
            # If user is logged in, verify they own the order
            try:
                order = Order.objects.get(order_number=order_number, user=request.user)
                logger.info(f"Found order {order_number} for authenticated user {request.user.id}")
            except Order.DoesNotExist:
                # Order not found for this user, try without user filter (for payment callbacks)
                logger.warning(f"Order {order_number} not found for user {request.user.id}, trying without user filter")
                order = Order.objects.get(order_number=order_number)
                logger.info(f"Found order {order_number} without user filter (belongs to user {order.user.id})")
        else:
            # If not logged in (coming from payment gateway), just get the order
            # This is safe because order_number is unique and hard to guess
            order = Order.objects.get(order_number=order_number)
            logger.info(f"Found order {order_number} for non-authenticated request")
            
            # IMPORTANT: Re-authenticate the user to maintain session
            # This prevents users from being logged out after SSLCommerz redirect
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=order.user.id)
                request.user = user
                request.session.create()
                request.session['_auth_user_id'] = str(user.pk)
                request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
                request.session['_auth_user_hash'] = user.get_session_auth_hash()
                request.session.modified = True
                logger.info(f"✅ User {user.id} re-authenticated after payment gateway redirect")
            except User.DoesNotExist:
                logger.warning(f"Could not re-authenticate user {order.user.id}")
            
            # Additional security: only allow access to recently confirmed/created orders (within last hour)
            # This prevents old orders from being accessed without login
            if order.confirmed_at:
                time_since_confirmation = timezone.now() - order.confirmed_at
                if time_since_confirmation.total_seconds() > 3600:  # 1 hour
                    # Order is too old, require login
                    logger.warning(f"Order {order_number} is too old (confirmed), redirecting to login")
                    messages.warning(request, 'Please log in to view your order.')
                    from django.urls import reverse
                    login_url = reverse(settings.LOGIN_URL)
                    return redirect(f"{login_url}?next={request.path}")
            elif order.created_at:
                time_since_creation = timezone.now() - order.created_at
                if time_since_creation.total_seconds() > 3600:  # 1 hour
                    # Order is too old, require login
                    logger.warning(f"Order {order_number} is too old (created), redirecting to login")
                    messages.warning(request, 'Please log in to view your order.')
                    from django.urls import reverse
                    login_url = reverse(settings.LOGIN_URL)
                    return redirect(f"{login_url}?next={request.path}")
    except Order.DoesNotExist:
        logger.error(f"Order {order_number} not found in database")
        messages.error(request, 'Order not found.')
        return redirect('books:home')
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_success.html', context)


@login_required
def my_orders(request):
    """User's orders list"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
    }
    return render(request, 'orders/my_orders.html', context)


@login_required
def order_detail(request, order_number):
    """Order detail view"""
    logger.info(f"order_detail called for order_number: {order_number}, user authenticated: {request.user.is_authenticated}")
    
    # Allow access to order details even without login for recent orders (payment callback scenario)
    try:
        if request.user.is_authenticated:
            # If user is logged in, verify they own the order
            try:
                order = Order.objects.get(order_number=order_number, user=request.user)
                logger.info(f"Found order {order_number} for authenticated user {request.user.id}")
            except Order.DoesNotExist:
                # Order not found for this user, try without user filter (for payment callbacks)
                logger.warning(f"Order {order_number} not found for user {request.user.id}, trying without user filter")
                order = Order.objects.get(order_number=order_number)
                logger.info(f"Found order {order_number} without user filter (belongs to user {order.user.id})")
                # If order belongs to different user, require login
                if order.user != request.user:
                    messages.warning(request, 'Please log in with the correct account to view this order.')
                    from django.urls import reverse
                    login_url = reverse(settings.LOGIN_URL)
                    return redirect(f"{login_url}?next={request.path}")
        else:
            # If not logged in (coming from payment gateway), allow access to recent orders
            order = Order.objects.get(order_number=order_number)
            logger.info(f"Found order {order_number} for non-authenticated request")
            
            # Additional security: only allow access to recently created orders (within last hour)
            # This prevents old orders from being accessed without login
            if order.confirmed_at:
                time_since_confirmation = timezone.now() - order.confirmed_at
                if time_since_confirmation.total_seconds() > 3600:  # 1 hour
                    logger.warning(f"Order {order_number} is too old (confirmed), redirecting to login")
                    messages.warning(request, 'Please log in to view your order.')
                    from django.urls import reverse
                    login_url = reverse(settings.LOGIN_URL)
                    return redirect(f"{login_url}?next={request.path}")
            elif order.created_at:
                time_since_creation = timezone.now() - order.created_at
                if time_since_creation.total_seconds() > 3600:  # 1 hour
                    logger.warning(f"Order {order_number} is too old (created), redirecting to login")
                    messages.warning(request, 'Please log in to view your order.')
                    from django.urls import reverse
                    login_url = reverse(settings.LOGIN_URL)
                    return redirect(f"{login_url}?next={request.path}")
    except Order.DoesNotExist:
        logger.error(f"Order {order_number} not found in database")
        messages.error(request, 'Order not found.')
        return redirect('books:home')
    
    order_items = OrderItem.objects.filter(order=order)
    status_history = OrderStatusHistory.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def cancel_order(request, order_number):
    """Cancel order"""
    from django.http import JsonResponse
    
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if not order.can_be_cancelled():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'This order cannot be cancelled.'})
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_detail', order_number=order_number)
    
    if request.method == 'POST':
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            notes='Cancelled by customer',
            changed_by=request.user
        )
        
        # Restore stock
        for item in order.items.all():
            if item.book:
                item.book.stock += item.quantity
                item.book.sales -= item.quantity
                item.book.save(update_fields=['stock', 'sales'])
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Order cancelled successfully.'})
        
        messages.success(request, 'Order cancelled successfully.')
        return redirect('orders:order_detail', order_number=order_number)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/cancel_order.html', context)


def track_order(request, order_number=None):
    """Track order by order number and phone"""
    order = None
    form = None
    
    # If order_number is provided in URL (from authenticated user)
    if order_number and request.user.is_authenticated:
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            messages.error(request, 'Order not found.')
    elif request.method == 'POST':
        # Guest tracking using form
        form = OrderTrackingForm(request.POST)
        if form.is_valid():
            order_number = form.cleaned_data['order_number']
            phone = form.cleaned_data['phone']
            
            try:
                order = Order.objects.get(order_number=order_number, shipping_phone=phone)
            except Order.DoesNotExist:
                messages.error(request, 'Order not found. Please check your order number and phone.')
    else:
        form = OrderTrackingForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'orders/track_order.html', context)


def gift_areas(request):
    """Return areas for a given city id (GET param: city_id)."""
    city_id = request.GET.get('city_id')
    try:
        if not city_id:
            return JsonResponse({'areas': []})
        areas = GiftArea.objects.filter(city_id=city_id).order_by('name')
        data = [{'id': a.id, 'name': a.name} for a in areas]
        return JsonResponse({'areas': data})
    except Exception as e:
        return JsonResponse({'areas': [], 'error': str(e)})


def gift_zones(request):
    """Return zones for a given area id (GET param: area_id)."""
    area_id = request.GET.get('area_id')
    try:
        if not area_id:
            return JsonResponse({'zones': []})
        zones = GiftZone.objects.filter(area_id=area_id).order_by('name')
        data = [{'id': z.id, 'name': z.name} for z in zones]
        return JsonResponse({'zones': data})
    except Exception as e:
        return JsonResponse({'zones': [], 'error': str(e)})


@login_required
def apply_coupon(request):
    """Apply coupon code"""
    from django.http import JsonResponse
    from .models import Coupon
    from books.models import Cart
    from decimal import Decimal
    
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        
        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})
        
        # Get coupon from database
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})
        
        # Check if coupon is valid
        if not coupon.is_valid():
            return JsonResponse({'success': False, 'message': 'This coupon has expired or is no longer active'})
        
        # Check if user can use this coupon (for authenticated users)
        if request.user.is_authenticated:
            can_use, message = coupon.can_be_used_by_user(request.user)
            if not can_use:
                return JsonResponse({'success': False, 'message': message})
        
        # Calculate cart subtotal
        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)
        else:
            cart_items = Cart.objects.filter(session_key=request.session.session_key)
        
        subtotal = sum(item.subtotal for item in cart_items)
        
        # Check minimum purchase amount
        if subtotal < coupon.min_purchase_amount:
            return JsonResponse({
                'success': False,
                'message': f'Minimum purchase amount of ৳{coupon.min_purchase_amount} required to use this coupon'
            })
        
        # Calculate discount
        discount = coupon.calculate_discount(subtotal)
        
        # Store coupon in session
        request.session['coupon_code'] = coupon.code
        request.session['coupon_id'] = coupon.id
        request.session['discount'] = float(discount)
        
        # Recalculate totals to return to frontend (so page doesn't need full reload)
        # Get shipping city from default address
        shipping_city = None
        if request.user.is_authenticated:
            default_address = Address.objects.filter(user=request.user, is_default=True).first()
            if default_address:
                shipping_city = default_address.city
        
        shipping = calculate_shipping_fee(shipping_city) if subtotal > 0 else Decimal('0.00')
        total = Decimal(subtotal) + shipping - Decimal(str(discount))

        return JsonResponse({
            'success': True,
            'message': f'Coupon applied! You saved ৳{discount:.2f}',
            'discount': float(discount),
            'coupon_code': coupon.code,
            'discount_display': f'৳{discount:.2f}',
            'subtotal': float(subtotal),
            'shipping_cost': float(shipping),
            'total': float(total),
            'cart_count': cart_items.count() if hasattr(cart_items, 'count') else len(cart_items)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def remove_coupon(request):
    """Remove applied coupon"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        # Remove coupon from session
        for key in ['coupon_code', 'coupon_id', 'discount']:
            if key in request.session:
                del request.session[key]
        # Recalculate totals and return updated summary so frontend can update without reload
        from books.models import Cart
        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)
        else:
            cart_items = Cart.objects.filter(session_key=request.session.session_key)

        subtotal = sum(item.subtotal for item in cart_items) if cart_items else 0
        
        # Get shipping city from default address for coupon removal
        shipping_city = None
        if request.user.is_authenticated:
            default_address = Address.objects.filter(user=request.user, is_default=True).first()
            if default_address:
                shipping_city = default_address.city
        
        shipping = calculate_shipping_fee(shipping_city) if subtotal > 0 else Decimal('0.00')
        discount = Decimal(str(request.session.get('discount', 0)))
        total = Decimal(subtotal) + shipping - discount

        return JsonResponse({
            'success': True,
            'message': 'Coupon removed successfully',
            'subtotal': float(subtotal),
            'shipping_cost': float(shipping),
            'total': float(total),
            'discount': float(discount),
            'cart_count': cart_items.count() if hasattr(cart_items, 'count') else len(cart_items)
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def invoice(request, order_number):
    """Generate and download order invoice as PDF"""
    from django.http import HttpResponse
    from .pdf_generator import generate_invoice_pdf
    
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Generate PDF using ReportLab
    pdf_content = generate_invoice_pdf(order)
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Invoice_{order.order_number}.pdf"'
    
    return response


@login_required
def email_invoice(request, order_number):
    """Email invoice to customer"""
    from django.http import JsonResponse
    
    # Verify this is a POST request and AJAX
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    # Get the order
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    try:
        # Send the email with invoice
        result = send_order_confirmation_email(order)
        
        if result:
            logger.info(f"✅ Invoice email sent successfully for order {order.order_number} to {order.user.email}")
            return JsonResponse({
                'success': True,
                'message': f'Invoice has been sent to {order.user.email}'
            })
        else:
            logger.warning(f"⚠️ Email function returned False for order {order.order_number}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to send invoice email. Please try again later.'
            }, status=500)
    
    except Exception as e:
        logger.error(f"❌ Failed to send invoice email for order {order.order_number}: {str(e)}")
        logger.exception("Full exception traceback:")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while sending the invoice. Please try again later.'
        }, status=500)
