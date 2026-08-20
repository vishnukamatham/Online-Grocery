from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.index, name='home'),

    # Products
    path('products/', views.products, name='products'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # Search
    path('search/', views.search, name='search'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('social-google-login/', views.social_google_login, name='social_google_login'),
    path('google-callback/', views.google_callback, name='google_callback'),
    path('excel/download/', views.download_excel_view, name='download_excel'),
    path('excel/sync/', views.sync_excel_view, name='sync_excel'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:pk>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:pk>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/',  views.payment_failed,  name='payment_failed'),
    path('payment/webhook/', views.payment_webhook, name='payment_webhook'),
    path('orders/', views.orders, name='orders'),

    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),

    # Account
    path('account/', views.account, name='account'),

    # About & Contact
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
