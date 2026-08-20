# 🛒 Grocery Online

A **full-stack grocery e-commerce website** built with Django, featuring product browsing, cart, wishlist, checkout, user authentication, and order management.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Django](https://img.shields.io/badge/Django-6.1-green?logo=django)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 🏠 **Homepage** — Hero section, categories, featured products, testimonials
- 🛍️ **Products** — Browse, filter by category, search by name
- 🔍 **Search** — Real-time product search using Django ORM
- 📦 **Product Details** — Full product info, related products
- 🔐 **Authentication** — Register, Login, Logout (Django auth)
- 🛒 **Shopping Cart** — Add/remove/update quantities, total calculation
- 💛 **Wishlist** — Save favourite products
- 💳 **Checkout** — Address form, order summary, place order
- 📋 **Orders** — View order history, track status
- 👤 **Account** — Dashboard with stats, recent orders, wishlist
- 🔧 **Admin Panel** — Manage products, categories, orders, users
- 📱 **Responsive** — Works on mobile, tablet, and desktop

---

## 🛠️ Technologies

| Technology | Purpose |
|---|---|
| Python 3.10+ | Backend language |
| Django 6.1 | Web framework |
| SQLite | Database |
| Django ORM | Database queries |
| Django Templates | HTML rendering |
| CSS3 | Styling & animations |
| JavaScript | Frontend interactivity |
| Pillow | Image handling |

---

## 📁 Project Structure

```
Online Grocery/
│
├── config/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── home/                    # Main app
│   ├── migrations/
│   ├── templates/home/      # All HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── products.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── wishlist.html
│   │   ├── checkout.html
│   │   ├── orders.html
│   │   ├── account.html
│   │   ├── register.html
│   │   ├── login.html
│   │   ├── about.html
│   │   └── contact.html
│   ├── static/home/         # CSS, JS, Images
│   │   ├── css/style.css
│   │   ├── js/script.js
│   │   └── images/
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # URL routing
│   ├── admin.py             # Admin configuration
│   └── context_processors.py
│
├── media/                   # Uploaded images
├── manage.py
├── requirements.txt
└── db.sqlite3
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or above
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/grocery-online.git
cd grocery-online

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create admin account
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

### 🌐 Open in Browser
```
http://127.0.0.1:8000/          # Homepage
http://127.0.0.1:8000/admin/    # Admin panel
```

---

## 🔑 Default Admin Credentials

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin@123` |
| Email | `admin@groceryonline.com` |

> ⚠️ Change the password after first login!

---

## 📸 Pages

| Page | URL |
|---|---|
| Home | `/` |
| Products | `/products/` |
| Product Detail | `/products/<id>/` |
| Search | `/search/?q=milk` |
| Cart | `/cart/` |
| Wishlist | `/wishlist/` |
| Checkout | `/checkout/` |
| Orders | `/orders/` |
| Account | `/account/` |
| Login | `/login/` |
| Register | `/register/` |
| About | `/about/` |
| Contact | `/contact/` |
| Admin | `/admin/` |

---

## 🎨 Design

- **Theme**: Orange (`#FF6B35`) + Dark (`#1a1a2e`) + White
- **Fonts**: Inter + Poppins (Google Fonts)
- **Icons**: Font Awesome 6
- **Design**: Glassmorphism, gradient buttons, card hover effects
- **Responsive**: Mobile-first responsive design

---

## 🔮 Future Improvements

- [ ] Payment gateway integration (Razorpay / Stripe)
- [ ] Email notifications for orders
- [ ] Product reviews and ratings by users
- [ ] Coupon/discount codes
- [ ] Admin analytics dashboard
- [ ] PWA (Progressive Web App)
- [ ] Deployment to Render / Railway / Heroku

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👨‍💻 Author

Made with ❤️ for learning Django full-stack development.
