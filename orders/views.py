from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from decimal import Decimal
from .models import Order, OrderItem, OrderStatusHistory
from .forms import CheckoutForm, OrderTrackingForm
from .email_utils import send_order_confirmation_email
from books.models import Cart
from accounts.models import Address
from payments.utils import initiate_payment
import logging

logger = logging.getLogger(__name__)


@login_required
def checkout(request):
    """Checkout view"""
    # Get cart items
    cart_items = Cart.objects.filter(user=request.user).select_related('book')
    
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('books:cart')
    
    # Check stock availability
    for item in cart_items:
        if item.quantity > item.book.stock:
            messages.error(request, f'{item.book.title} has insufficient stock.')
            return redirect('books:cart')
    
    # Calculate totals
    subtotal = sum(item.subtotal for item in cart_items)
    shipping = Decimal('60.00')  # Flat rate
    
    # Get coupon discount from session
    discount = Decimal(str(request.session.get('discount', 0)))
    coupon_code = request.session.get('coupon_code', None)
    
    total = subtotal + shipping - discount
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Get or create shipping address
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
                **shipping_data
            )
            
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
        form = CheckoutForm(user=request.user)
    
    # Get user addresses
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
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
    """Order success page - accessible without login for payment callbacks"""
    # Try to get order - allow access for payment callbacks even if user is not logged in
    try:
        if request.user.is_authenticated:
            # If user is logged in, verify they own the order
            order = get_object_or_404(Order, order_number=order_number, user=request.user)
        else:
            # If not logged in (coming from payment gateway), just get the order
            # This is safe because order_number is unique and hard to guess
            order = get_object_or_404(Order, order_number=order_number)
            
            # Additional security: only allow access to recently confirmed orders (within last hour)
            # This prevents old orders from being accessed without login
            if order.confirmed_at:
                time_since_confirmation = timezone.now() - order.confirmed_at
                if time_since_confirmation.total_seconds() > 3600:  # 1 hour
                    # Order is too old, require login
                    messages.warning(request, 'Please log in to view your order.')
                    return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            elif order.created_at:
                time_since_creation = timezone.now() - order.created_at
                if time_since_creation.total_seconds() > 3600:  # 1 hour
                    # Order is too old, require login
                    messages.warning(request, 'Please log in to view your order.')
                    return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    except Order.DoesNotExist:
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
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
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
        
        return JsonResponse({
            'success': True,
            'message': f'Coupon applied! You saved ৳{discount:.2f}',
            'discount': float(discount),
            'coupon_code': coupon.code,
            'discount_display': f'৳{discount:.2f}'
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
        
        return JsonResponse({
            'success': True,
            'message': 'Coupon removed successfully'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def invoice(request, order_number):
    """Generate order invoice"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/invoice.html', context)
