from django.conf import settings

def cart_wishlist_count(request):
    cart_count = 0
    wishlist_count = 0
    if request.user.is_authenticated:
        from .models import Cart, Wishlist
        cart_count = Cart.objects.filter(user=request.user).count()
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'contact_email': getattr(settings, 'CONTACT_EMAIL', 'contact@groceryonline.com'),
        'contact_phone': getattr(settings, 'CONTACT_PHONE', '+91 83320 20246'),
        'contact_address': getattr(settings, 'CONTACT_ADDRESS', 'Hyderabad, India'),
        'google_client_id': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
    }
