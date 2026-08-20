from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from .models import Category, Product, Cart, Wishlist, Order, OrderItem, Coupon, ServiceablePincode
from django.utils import timezone
from decimal import Decimal
import razorpay
import json


# ─────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────
def index(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_featured=True, stock__gt=0)[:8]
    all_products = Product.objects.filter(stock__gt=0)[:8]
    products = featured_products if featured_products.exists() else all_products
    context = {
        'categories': categories,
        'featured_products': products,
    }
    return render(request, 'home/index.html', context)


# ─────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────
def products(request):
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')
    all_categories = Category.objects.all()
    product_list = Product.objects.filter(stock__gt=0)

    if query:
        product_list = product_list.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        product_list = product_list.filter(category=selected_category)

    context = {
        'products': product_list,
        'categories': all_categories,
        'selected_category': selected_category,
        'query': query,
    }
    return render(request, 'home/products.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(pk=pk)[:4]

    in_wishlist = False
    in_cart = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        in_cart = Cart.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
        'in_cart': in_cart,
        'star_range': range(1, 6),
    }
    return render(request, 'home/product_detail.html', context)


# ─────────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────────
def search(request):
    query = request.GET.get('q', '')
    product_list = Product.objects.none()
    if query:
        product_list = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    context = {'products': product_list, 'query': query}
    return render(request, 'home/search.html', context)


# ─────────────────────────────────────────────
#  AUTH — REGISTER / LOGIN / LOGOUT
# ─────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        if not all([first_name, username, email, password1, password2]):
            messages.error(request, 'All fields are required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            login(request, user)
            messages.success(request, f'Welcome, {first_name}! Account created successfully.')
            return redirect('home')

    return render(request, 'home/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'home/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ─────────────────────────────────────────────
#  CART
# ─────────────────────────────────────────────
@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    subtotal = sum(item.get_subtotal() for item in cart_items)
    delivery_charge = Decimal('40.00') if subtotal < 200 and subtotal > 0 else Decimal('0.00')
    total = subtotal + delivery_charge
    free_delivery_remaining = max(Decimal('200.00') - subtotal, Decimal('0.00'))
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_charge': delivery_charge,
        'total': total,
        'free_delivery_remaining': free_delivery_remaining,
    }
    return render(request, 'home/cart.html', context)


@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not product.is_available():
        messages.error(request, f'Sorry, {product.name} is out of stock.')
        return redirect(request.META.get('HTTP_REFERER', 'products'))

    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Added another {product.name} to cart.')
        else:
            messages.warning(request, f'Maximum stock reached for {product.name}.')
    else:
        messages.success(request, f'{product.name} added to cart!')

    return redirect(request.META.get('HTTP_REFERER', 'products'))


@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(Cart, pk=pk, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def update_cart(request, pk):
    cart_item = get_object_or_404(Cart, pk=pk, user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, 'Item removed from cart.')
    return redirect('cart')


# ─────────────────────────────────────────────
#  WISHLIST
# ─────────────────────────────────────────────
@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'home/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f'{product.name} added to wishlist!')
    else:
        messages.info(request, f'{product.name} is already in your wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'products'))


@login_required
def remove_from_wishlist(request, pk):
    wishlist_item = get_object_or_404(Wishlist, pk=pk, user=request.user)
    wishlist_item.delete()
    messages.success(request, 'Item removed from wishlist.')
    return redirect('wishlist')


# ─────────────────────────────────────────────
#  CHECKOUT  (with Razorpay)
# ─────────────────────────────────────────────
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty. Add products before checkout.')
        return redirect('cart')

    subtotal = sum(item.get_subtotal() for item in cart_items)
    delivery_charge = Decimal('40.00') if subtotal < 200 else Decimal('0.00')
    
    # Coupon validation
    coupon_code = request.session.get('coupon_code')
    coupon = None
    discount_amount = Decimal('0.00')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(
                code__iexact=coupon_code,
                active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            discount_amount = Decimal(str(round((subtotal * coupon.discount_percent) / 100, 2)))
        except Coupon.DoesNotExist:
            request.session.pop('coupon_code', None)

    total = max(subtotal + delivery_charge - discount_amount, Decimal('0.00'))

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email     = request.POST.get('email', '').strip()
        phone     = request.POST.get('phone', '').strip()
        address   = request.POST.get('address', '').strip()
        city      = request.POST.get('city', '').strip()
        state     = request.POST.get('state', '').strip()
        pincode   = request.POST.get('pincode', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')

        if not all([full_name, email, phone, address, city, state, pincode]):
            messages.error(request, 'Please fill in all fields.')
            context = {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'delivery_charge': delivery_charge,
                'discount_amount': discount_amount,
                'coupon': coupon,
                'total': total,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
            }
            return render(request, 'home/checkout.html', context)

        if not pincode.isdigit() or len(pincode) != 6:
            messages.error(request, 'Pincode must be exactly 6 digits.')
            context = {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'delivery_charge': delivery_charge,
                'discount_amount': discount_amount,
                'coupon': coupon,
                'total': total,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
            }
            return render(request, 'home/checkout.html', context)

        # Serviceable pincode verification
        if ServiceablePincode.objects.exists() and not ServiceablePincode.objects.filter(pincode=pincode).exists():
            messages.error(request, f'Sorry, we do not deliver to pincode {pincode} yet.')
            context = {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'delivery_charge': delivery_charge,
                'discount_amount': discount_amount,
                'coupon': coupon,
                'total': total,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
            }
            return render(request, 'home/checkout.html', context)

        # Save delivery info in session for Razorpay flow
        request.session['checkout_data'] = {
            'full_name': full_name, 'email': email, 'phone': phone,
            'address': address, 'city': city, 'state': state, 'pincode': pincode,
        }

        if payment_method == 'online':
            # ── Check if Razorpay keys are configured ──
            if 'YourKeyIdHere' in settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_ID.startswith('rzp_'):
                messages.error(request, 'Online payment is not configured yet. Please use Cash on Delivery or contact the admin to set up Razorpay keys.')
                context = {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'delivery_charge': delivery_charge,
                    'discount_amount': discount_amount,
                    'coupon': coupon,
                    'total': total,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                }
                return render(request, 'home/checkout.html', context)

            # ── Create Razorpay order ──
            try:
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
                amount_paise = int(total * 100)  # Razorpay uses paise (1 INR = 100 paise)
                razorpay_order = client.order.create({
                    'amount':   amount_paise,
                    'currency': 'INR',
                    'payment_capture': 1,
                })
            except Exception as e:
                messages.error(request, f'Payment gateway error: Please check your Razorpay API keys. Details: {str(e)}')
                context = {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'delivery_charge': delivery_charge,
                    'discount_amount': discount_amount,
                    'coupon': coupon,
                    'total': total,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                }
                return render(request, 'home/checkout.html', context)

            # ── Create Django Order in database in Pending status PRIOR to payment ──
            from django.db import transaction
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        coupon=coupon,
                        discount_amount=discount_amount,
                        total_amount=total,
                        delivery_charge=delivery_charge,
                        full_name=full_name, email=email, phone=phone,
                        address=address, city=city, state=state, pincode=pincode,
                        payment_method='Online', payment_status='Pending',
                        status='pending',
                        razorpay_order_id=razorpay_order['id'],
                    )
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order, product=item.product,
                            product_name=item.product.name,
                            quantity=item.quantity, price=item.product.price,
                        )
            except Exception as e:
                messages.error(request, f'Failed to generate order records: {str(e)}')
                context = {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'delivery_charge': delivery_charge,
                    'discount_amount': discount_amount,
                    'coupon': coupon,
                    'total': total,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                }
                return render(request, 'home/checkout.html', context)

            context = {
                'cart_items':        cart_items,
                'subtotal':          subtotal,
                'delivery_charge':   delivery_charge,
                'discount_amount':   discount_amount,
                'coupon':            coupon,
                'total':             total,
                'razorpay_key':      settings.RAZORPAY_KEY_ID,
                'razorpay_order_id': razorpay_order['id'],
                'amount_paise':      amount_paise,
                'full_name':         full_name,
                'email':             email,
                'phone':             phone,
                'show_payment':      True,
            }
            return render(request, 'home/checkout.html', context)

        else:
            # ── Cash on Delivery ──
            order = Order.objects.create(
                user=request.user,
                coupon=coupon,
                discount_amount=discount_amount,
                total_amount=total,
                delivery_charge=delivery_charge,
                full_name=full_name, email=email, phone=phone,
                address=address, city=city, state=state, pincode=pincode,
                payment_method='COD', payment_status='Pending',
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order, product=item.product,
                    product_name=item.product.name,
                    quantity=item.quantity, price=item.product.price,
                )
                item.product.stock -= item.quantity
                item.product.save()
            cart_items.delete()
            request.session.pop('coupon_code', None)
            messages.success(request, f'Order #{order.id} placed! Pay cash on delivery.')
            return redirect('order_detail', pk=order.pk)

    context = {
        'cart_items':   cart_items,
        'subtotal':     subtotal,
        'delivery_charge': delivery_charge,
        'discount_amount': discount_amount,
        'coupon':       coupon,
        'total':        total,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'home/checkout.html', context)


# ─────────────────────────────────────────────
#  PAYMENT SUCCESS (Razorpay callback)
# ─────────────────────────────────────────────
@login_required
@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id   = request.POST.get('razorpay_order_id', '')
        razorpay_signature  = request.POST.get('razorpay_signature', '')

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # Verify signature
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id':   razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature':  razorpay_signature,
            })
            payment_verified = True
        except razorpay.errors.SignatureVerificationError:
            payment_verified = False

        if payment_verified:
            from django.db import transaction
            try:
                with transaction.atomic():
                    # Select for update to prevent race conditions (locking)
                    order = Order.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
                    
                    if order.payment_status != 'Paid':
                        order.payment_status = 'Paid'
                        order.razorpay_payment_id = razorpay_payment_id
                        order.status = 'confirmed'
                        order.save()
                        
                        # Deduct stock
                        for item in order.items.all():
                            if item.product:
                                item.product.stock -= item.quantity
                                item.product.save()
                        
                        # Clear user's cart
                        Cart.objects.filter(user=order.user).delete()
                        
                        # Clear session variables
                        request.session.pop('coupon_code', None)
                        request.session.pop('checkout_data', None)
                        
                        messages.success(request, f'Payment successful! Order #{order.id} confirmed.')
                        return redirect('order_detail', pk=order.pk)
                    else:
                        messages.info(request, f'Order #{order.id} is already processed.')
                        return redirect('order_detail', pk=order.pk)
            except Order.DoesNotExist:
                messages.error(request, 'Order record not found for verification.')
                return redirect('checkout')
        else:
            # Signature verification failed
            try:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.payment_status = 'Failed'
                order.status = 'cancelled'
                order.save()
            except Order.DoesNotExist:
                pass
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('checkout')

    return redirect('checkout')


# ─────────────────────────────────────────────
#  PAYMENT WEBHOOK (Razorpay Event Receiver)
# ─────────────────────────────────────────────
@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        payload = request.body.decode('utf-8')
        sig_header = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
        
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        try:
            webhook_secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'test_webhook_secret')
            client.utility.verify_webhook_signature(payload, sig_header, webhook_secret)
            
            data = json.loads(payload)
            event = data.get('event')
            
            if event in ['payment.captured', 'order.paid']:
                payment_entity = data['payload']['payment']['entity']
                razorpay_order_id = payment_entity.get('order_id')
                razorpay_payment_id = payment_entity.get('id')
                
                if razorpay_order_id:
                    from django.db import transaction
                    with transaction.atomic():
                        try:
                            order = Order.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
                            if order.payment_status != 'Paid':
                                order.payment_status = 'Paid'
                                order.razorpay_payment_id = razorpay_payment_id
                                order.status = 'confirmed'
                                order.save()
                                
                                # Deduct stock
                                for item in order.items.all():
                                    if item.product:
                                        item.product.stock -= item.quantity
                                        item.product.save()
                                
                                # Clear cart
                                Cart.objects.filter(user=order.user).delete()
                        except Order.DoesNotExist:
                            pass
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)


# ─────────────────────────────────────────────
#  PAYMENT FAILED
# ─────────────────────────────────────────────
@login_required
def payment_failed(request):
    messages.error(request, 'Payment was cancelled or failed. Please try again.')
    return redirect('checkout')


# ─────────────────────────────────────────────
#  COUPONS
# ─────────────────────────────────────────────
@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        if not code:
            messages.warning(request, 'Please enter a coupon code.')
            return redirect('checkout')
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            request.session['coupon_code'] = coupon.code
            messages.success(request, f'Coupon "{coupon.code}" applied! ({coupon.discount_percent}% off)')
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid, expired, or inactive coupon code.')
    return redirect('checkout')


@login_required
def remove_coupon(request):
    request.session.pop('coupon_code', None)
    messages.info(request, 'Coupon removed.')
    return redirect('checkout')


# ─────────────────────────────────────────────
#  ORDERS
# ─────────────────────────────────────────────
@login_required
def orders(request):
    from django.utils import timezone
    # Automatically confirm pending orders after 2 minutes
    pending_orders = Order.objects.filter(user=request.user, status='pending')
    for order in pending_orders:
        time_diff = timezone.now() - order.created_at
        if time_diff.total_seconds() >= 120:
            order.status = 'confirmed'
            order.save(update_fields=['status'])

    user_orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'home/orders.html', {'orders': user_orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    from django.utils import timezone
    remaining_seconds = 0
    if order.status == 'pending':
        time_diff = timezone.now() - order.created_at
        elapsed = time_diff.total_seconds()
        if elapsed >= 120:
            order.status = 'confirmed'
            order.save(update_fields=['status'])
        else:
            remaining_seconds = int(120 - elapsed)
            
    return render(request, 'home/order_detail.html', {'order': order, 'remaining_seconds': remaining_seconds})


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.can_cancel():
        # Restore stock levels
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        messages.success(request, f'Order #{order.id} has been cancelled successfully.')
    else:
        messages.error(request, 'This order cannot be cancelled as it is already confirmed or the 2-minute cancellation window has expired.')
    return redirect('order_detail', pk=order.pk)


# ─────────────────────────────────────────────
#  ACCOUNT
# ─────────────────────────────────────────────
@login_required
def account(request):
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()
            email      = request.POST.get('email', '').strip()
            
            if not first_name or not email:
                messages.error(request, 'First name and Email are required.')
            elif User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request, 'This email is already in use by another account.')
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                messages.success(request, 'Profile updated successfully.')
            return redirect('account')
            
        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password     = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not current_password or not new_password or not confirm_password:
                messages.error(request, 'All fields are required.')
            elif not request.user.check_password(current_password):
                messages.error(request, 'Incorrect current password.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
            else:
                from django.contrib.auth import update_session_auth_hash
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
            return redirect('account')

    user_orders = Order.objects.filter(user=request.user)[:5]
    wishlist_items = Wishlist.objects.filter(user=request.user)[:4]
    cart_items = Cart.objects.filter(user=request.user)
    context = {
        'user_orders': user_orders,
        'wishlist_items': wishlist_items,
        'cart_items': cart_items,
    }
    return render(request, 'home/account.html', context)


# ─────────────────────────────────────────────
#  ABOUT / CONTACT
# ─────────────────────────────────────────────
def about(request):
    return render(request, 'home/about.html')


def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'home/contact.html')

        # ── Send real email to your Gmail ──
        try:
            from django.core.mail import send_mail
            full_message = f"""
New Contact Form Message — Grocery Online
==========================================

From    : {name}
Email   : {email}
Subject : {subject}

Message:
{message}

==========================================
Sent from Grocery Online Contact Form
            """.strip()

            send_mail(
                subject=f'[Grocery Online] {subject}',
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, f'Thank you {name}! Your message has been sent. We will reply to {email} soon.')
        except Exception as e:
            messages.error(request, 'Sorry, message could not be sent right now. Please email us directly at vishnulovely338@gmail.com')

        return redirect('contact')
    return render(request, 'home/contact.html')


def social_google_login(request):
    user, created = User.objects.get_or_create(
        username='google_user',
        defaults={
            'email': 'user@gmail.com',
            'first_name': 'Google',
            'last_name': 'User'
        }
    )
    if created:
        user.set_unusable_password()
        user.save()
    
    login(request, user)
    messages.success(request, "Welcome, Google User! Successfully signed in with Google.")
    return redirect('home')


import urllib.request
import json

@csrf_exempt
def google_callback(request):
    if request.method == 'POST':
        token = request.POST.get('credential')
        if not token:
            messages.error(request, 'Google sign-in failed: No credential returned.')
            return redirect('login')
        
        # Verify the token with Google
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                user_info = json.loads(response.read().decode())
                
            # Verify target client ID
            aud = user_info.get('aud')
            if aud != settings.GOOGLE_CLIENT_ID:
                messages.error(request, 'Google sign-in failed: Client ID mismatch.')
                return redirect('login')
                
            # Retrieve email and details
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            
            if not email:
                messages.error(request, 'Google sign-in failed: Email not provided.')
                return redirect('login')
                
            # Find or create user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                try:
                    existing_user = User.objects.get(username=username)
                    if existing_user.email == email:
                        user = existing_user
                        break
                except User.DoesNotExist:
                    pass
                username = f"{base_username}{counter}"
                counter += 1
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                user.set_unusable_password()
                user.save()
                
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}! Logged in via Google.')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Google sign-in failed: Verification error. {str(e)}')
            return redirect('login')
            
    return redirect('login')


from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404
from .excel_utils import FILEPATH, export_all_to_excel

@staff_member_required
def download_excel_view(request):
    import os
    if not os.path.exists(FILEPATH):
        try:
            export_all_to_excel()
        except Exception as e:
            messages.error(request, f"Could not generate Excel file: {str(e)}")
            return redirect('admin:index')
            
    try:
        response = FileResponse(open(FILEPATH, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Grocery_Online_Data.xlsx"'
        return response
    except Exception as e:
        raise Http404(f"Error accessing file: {str(e)}")

@staff_member_required
def sync_excel_view(request):
    try:
        export_all_to_excel()
        messages.success(request, "Excel data successfully synchronized with current database records.")
    except Exception as e:
        messages.error(request, f"Excel synchronization failed: {str(e)}")
    return redirect('admin:index')
