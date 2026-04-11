# 🛒 ONGO — E-Commerce Platform

ONGO is a fully functional e-commerce web application built with Django and PostgreSQL/MySQL. It supports the complete online shopping experience — from browsing products and managing a cart to secure checkout, user referrals, and an admin dashboard.

---

## 🚀 Features

- **Product Listing & Browsing** — Browse products with filtering and search capabilities
- **Shopping Cart** — Add, update, and remove items before checkout
- **User Authentication** — Register, log in, and manage user accounts securely
- **Payment Integration** — Seamless and secure online payment processing
- **Admin Dashboard** — Manage products, orders, and users from a dedicated admin panel
- **Product Reviews** — Authenticated users can leave reviews and ratings on products
- **User Referral System** — Users can refer others and earn rewards

---

## 🛠️ Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python, Django          |
| Database   | MySQL / PostgreSQL       |
| Frontend   | HTML, CSS, JavaScript   |

---

## 📁 Project Structure

```
ONGO-E-Commerce-Project/
├── manage.py
├── requirements.txt
├── ongo/                  # Core Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── products/              # Product listing and detail views
├── cart/                  # Shopping cart logic
├── accounts/              # User auth and referral system
├── orders/                # Order management
├── payments/              # Payment integration
├── reviews/               # Product review system
├── templates/             # HTML templates
└── static/                # CSS, JS, and images
```

> Note: Folder names may vary slightly from the actual repo structure.

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.8+
- pip
- MySQL or PostgreSQL installed and running

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Don-Soby-2007/ONGO-E-Commerce-Project.git
   cd ONGO-E-Commerce-Project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database**

   Update `ongo/settings.py` with your database credentials:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',  # or 'mysql'
           'NAME': 'ongo_db',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',  # or '3306' for MySQL
       }
   }
   ```

5. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. Open your browser and go to `http://127.0.0.1:8000`

---

## 🔑 Admin Panel

Access the Django admin dashboard at:
```
http://127.0.0.1:8000/admin
```
Log in with the superuser credentials you created above.

---

## 💳 Payment Integration

ONGO includes payment gateway integration. Make sure to configure your payment credentials (API keys) in the environment variables or `settings.py` before running the application in production.

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request

---

## 📄 License

This project is open source. Feel free to use and modify it for educational or personal purposes.

---

## 👤 Author

**Don Soby**
- GitHub: [@Don-Soby-2007](https://github.com/Don-Soby-2007)
