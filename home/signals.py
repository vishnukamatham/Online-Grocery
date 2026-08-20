from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Product, Order, OrderItem, Cart, Wishlist
from .excel_utils import sync_model_to_excel

# Categories
@receiver(post_save, sender=Category)
def category_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Categories', instance, 'save')

@receiver(post_delete, sender=Category)
def category_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Categories', instance, 'delete')


# Products
@receiver(post_save, sender=Product)
def product_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Products', instance, 'save')

@receiver(post_delete, sender=Product)
def product_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Products', instance, 'delete')


# Users
@receiver(post_save, sender=User)
def user_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Users', instance, 'save')

@receiver(post_delete, sender=User)
def user_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Users', instance, 'delete')


# Orders
@receiver(post_save, sender=Order)
def order_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Orders', instance, 'save')

@receiver(post_delete, sender=Order)
def order_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Orders', instance, 'delete')


# OrderItems
@receiver(post_save, sender=OrderItem)
def order_item_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Order_Items', instance, 'save')

@receiver(post_delete, sender=OrderItem)
def order_item_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Order_Items', instance, 'delete')


# Carts
@receiver(post_save, sender=Cart)
def cart_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Carts', instance, 'save')

@receiver(post_delete, sender=Cart)
def cart_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Carts', instance, 'delete')


# Wishlists
@receiver(post_save, sender=Wishlist)
def wishlist_save_signal(sender, instance, **kwargs):
    sync_model_to_excel('Wishlists', instance, 'save')

@receiver(post_delete, sender=Wishlist)
def wishlist_delete_signal(sender, instance, **kwargs):
    sync_model_to_excel('Wishlists', instance, 'delete')
