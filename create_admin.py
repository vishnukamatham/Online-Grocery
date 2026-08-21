import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

# List of admin users to ensure exist in the database
admins = [
    {'username': 'vishnu', 'email': 'vishnu@groceryonline.com'},
    {'username': 'admin', 'email': 'admin@groceryonline.com'},
]

for admin_info in admins:
    user, created = User.objects.get_or_create(username=admin_info['username'])
    user.email = admin_info['email']
    user.set_password('admin@123')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    if created:
        print(f"Created superuser '{admin_info['username']}' with password 'admin@123'")
    else:
        print(f"Updated superuser '{admin_info['username']}' password to 'admin@123'")
