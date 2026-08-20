from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
import datetime
import os

from .models import Category, Product, Cart, Wishlist, Coupon, Order, OrderItem, ServiceablePincode
from .excel_utils import SHEETS_CONFIG

class GroceryBackendTestBase(TestCase):
    def setUp(self):
        # Prevent test signals from writing to the real production Excel workbook
        self.excel_patcher = patch('home.signals.sync_model_to_excel')
        self.mock_excel_sync = self.excel_patcher.start()
        
        # Setup basic data
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        self.category = Category.objects.create(name='Fruits & Vegetables', slug='fruits-vegetables')
        self.product = Product.objects.create(
            name='Fresh Bananas',
            category=self.category,
            price=Decimal('50.00'),
            stock=100,
            is_featured=True
        )

    def tearDown(self):
        self.excel_patcher.stop()

class AuthTests(GroceryBackendTestBase):
    def test_user_registration_success(self):
        response = self.client.post(reverse('register'), {
            'first_name': 'New',
            'last_name': 'User',
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_registration_mismatch_passwords(self):
        response = self.client.post(reverse('register'), {
            'first_name': 'New',
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password1': 'newpassword123',
            'password2': 'differentpassword'
        })
        self.assertEqual(response.status_code, 200) # Re-renders page with error
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_user_login_logout(self):
        login_success = self.client.login(username='testuser', password='testpassword123')
        self.assertTrue(login_success)
        
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

class ProductCatalogueTests(GroceryBackendTestBase):
    def test_product_listing(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fresh Bananas')

    def test_product_detail(self):
        response = self.client.get(reverse('product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fresh Bananas')

    def test_category_filtering(self):
        response = self.client.get(reverse('products') + f'?category={self.category.slug}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fresh Bananas')

    def test_search(self):
        response = self.client.get(reverse('search') + '?q=Bananas')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fresh Bananas')

class CartTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')

    def test_cart_operations(self):
        # Add to cart
        response = self.client.get(reverse('add_to_cart', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cart.objects.filter(user=self.user, product=self.product).exists())
        
        cart_item = Cart.objects.get(user=self.user, product=self.product)
        self.assertEqual(cart_item.quantity, 1)

        # Update cart quantity
        response = self.client.post(reverse('update_cart', args=[cart_item.pk]), {'action': 'increase'})
        self.assertEqual(response.status_code, 302)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)

        # Cart subtotal check
        self.assertEqual(cart_item.get_subtotal(), Decimal('100.00'))

        # Remove from cart
        response = self.client.get(reverse('remove_from_cart', args=[cart_item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cart.objects.filter(user=self.user, product=self.product).exists())

class WishlistTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')

    def test_wishlist_operations(self):
        # Add to wishlist
        response = self.client.get(reverse('add_to_wishlist', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())
        
        wishlist_item = Wishlist.objects.get(user=self.user, product=self.product)
        
        # Remove from wishlist
        response = self.client.get(reverse('remove_from_wishlist', args=[wishlist_item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())

class CouponTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')
        # Create active and expired coupons
        self.active_coupon = Coupon.objects.create(
            code='SAVE10',
            discount_percent=10,
            active=True,
            valid_from=timezone.now() - datetime.timedelta(days=1),
            valid_to=timezone.now() + datetime.timedelta(days=2)
        )
        self.expired_coupon = Coupon.objects.create(
            code='EXPIRED',
            discount_percent=20,
            active=True,
            valid_from=timezone.now() - datetime.timedelta(days=5),
            valid_to=timezone.now() - datetime.timedelta(days=1)
        )

    def test_apply_valid_coupon(self):
        response = self.client.post(reverse('apply_coupon'), {'coupon_code': 'SAVE10'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('coupon_code'), 'SAVE10')

    def test_apply_expired_coupon(self):
        response = self.client.post(reverse('apply_coupon'), {'coupon_code': 'EXPIRED'})
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get('coupon_code'))

class CheckoutCODTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')
        Cart.objects.create(user=self.user, product=self.product, quantity=2)

    def test_cod_checkout_creates_order_and_deducts_stock(self):
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Test Checkout',
            'email': 'checkout@example.com',
            'phone': '1234567890',
            'address': '123 Street Name',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'pincode': '500001',
            'payment_method': 'cod'
        })
        # Verifies redirect to order_detail
        self.assertEqual(response.status_code, 302)
        
        # Verify order exists
        order = Order.objects.filter(user=self.user, payment_method='COD').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, 'Pending')
        
        # Verify order items
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 2)
        
        # Verify stock level is decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 98) # 100 - 2
        
        # Verify cart was cleared
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

class PincodeTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')
        Cart.objects.create(user=self.user, product=self.product, quantity=1)

    def test_checkout_allowed_serviceable_pincode(self):
        ServiceablePincode.objects.create(pincode='500001', city='Hyderabad', state='TS')
        
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Test Pincode',
            'email': 'pincode@example.com',
            'phone': '1234567890',
            'address': '123 Street Name',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'pincode': '500001',
            'payment_method': 'cod'
        })
        self.assertEqual(response.status_code, 302) # Success Redirect

    def test_checkout_blocked_unserviceable_pincode(self):
        ServiceablePincode.objects.create(pincode='500001', city='Hyderabad', state='TS')
        
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Test Pincode',
            'email': 'pincode@example.com',
            'phone': '1234567890',
            'address': '123 Street Name',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'pincode': '560001', # Not serviceable
            'payment_method': 'cod'
        })
        self.assertEqual(response.status_code, 200) # Renders page with error
        self.assertFalse(Order.objects.filter(user=self.user).exists())

class RazorpayCheckoutTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')
        Cart.objects.create(user=self.user, product=self.product, quantity=2)

    @patch('razorpay.Client')
    def test_online_payment_checkout_generates_pending_order(self, mock_razorpay):
        # Mock Razorpay API response
        mock_instance = MagicMock()
        mock_instance.order.create.return_value = {'id': 'order_mock_123'}
        mock_razorpay.return_value = mock_instance

        response = self.client.post(reverse('checkout'), {
            'full_name': 'Test Online Checkout',
            'email': 'online@example.com',
            'phone': '1234567890',
            'address': '123 Street Name',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'pincode': '500001',
            'payment_method': 'online'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'order_mock_123')

        # Order must exist in pending state
        order = Order.objects.filter(razorpay_order_id='order_mock_123').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.payment_status, 'Pending')
        
        # Verify stock has NOT been decremented yet
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 100)

    @patch('razorpay.Client')
    def test_payment_success_verification_confirm_order_and_deducts_stock(self, mock_razorpay):
        # Setup pending order
        order = Order.objects.create(
            user=self.user, total_amount=Decimal('100.00'), delivery_charge=Decimal('0.00'),
            full_name='Test', email='test@example.com', phone='12345',
            address='123', city='Hyd', state='TS', pincode='500001',
            payment_method='Online', payment_status='Pending',
            razorpay_order_id='order_mock_success'
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=Decimal('50.00'))

        # Mock successful signature check
        mock_instance = MagicMock()
        mock_instance.utility.verify_payment_signature.return_value = True
        mock_razorpay.return_value = mock_instance

        response = self.client.post(reverse('payment_success'), {
            'razorpay_payment_id': 'pay_mock_123',
            'razorpay_order_id': 'order_mock_success',
            'razorpay_signature': 'sig_mock_123'
        })
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'Paid')
        self.assertEqual(order.status, 'confirmed')

        # Stock is decremented
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 98)

    @patch('razorpay.Client')
    def test_duplicate_success_call_prevent_duplicate_stock_reduction(self, mock_razorpay):
        # Setup order that is already Paid
        order = Order.objects.create(
            user=self.user, total_amount=Decimal('100.00'), delivery_charge=Decimal('0.00'),
            full_name='Test', email='test@example.com', phone='12345',
            address='123', city='Hyd', state='TS', pincode='500001',
            payment_method='Online', payment_status='Paid',
            razorpay_order_id='order_mock_duplicate'
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=Decimal('50.00'))

        mock_instance = MagicMock()
        mock_instance.utility.verify_payment_signature.return_value = True
        mock_razorpay.return_value = mock_instance

        # Call success endpoint
        response = self.client.post(reverse('payment_success'), {
            'razorpay_payment_id': 'pay_mock_123',
            'razorpay_order_id': 'order_mock_duplicate',
            'razorpay_signature': 'sig_mock_123'
        })
        self.assertEqual(response.status_code, 302)

        # Product stock remains unchanged
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 100)

class OrderCancellationTests(GroceryBackendTestBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser', password='testpassword123')
        self.order = Order.objects.create(
            user=self.user, total_amount=Decimal('100.00'), delivery_charge=Decimal('0.00'),
            full_name='Test', email='test@example.com', phone='12345',
            address='123', city='Hyd', state='TS', pincode='500001',
            payment_method='COD', payment_status='Pending', status='pending'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, product=self.product, quantity=5, price=Decimal('50.00')
        )
        # Deduct stock as COD checkout does
        self.product.stock -= 5
        self.product.save()

    def test_cancel_order_within_window_restores_stock(self):
        # Call cancellation endpoint
        response = self.client.get(reverse('cancel_order', args=[self.order.pk]))
        self.assertEqual(response.status_code, 302)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
        
        # Verify stock was restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 100) # 95 + 5

class AdminTests(GroceryBackendTestBase):
    def test_admin_models_are_registered(self):
        from django.contrib import admin
        registered_models = admin.site._registry.keys()
        self.assertIn(Category, registered_models)
        self.assertIn(Product, registered_models)
        self.assertIn(Order, registered_models)
        self.assertIn(ServiceablePincode, registered_models)
