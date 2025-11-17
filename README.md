# 📚 BookStore - Django E-Commerce Application

A modern, feature-rich online bookstore application built with Django, offering a seamless shopping experience with book rentals, wishlists, secure payments, and professional UI/UX design.

![Django](https://img.shields.io/badge/Django-4.2.7-darkgreen)
![Python](https://img.shields.io/badge/Python-3.12.10-blue)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange)
![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 Features

### Core Features
- 📖 **Book Catalog** - Browse and search thousands of books with advanced filtering
- 🛒 **Shopping Cart** - Add/remove books with quantity management
- 🎁 **Wishlist** - Save favorite books for later purchase
- 💳 **Secure Payments** - SSLCommerz payment gateway integration
- 📱 **Book Rentals** - Rent books with flexible rental periods
- ⭐ **Rating & Reviews** - User reviews and ratings system
- 🏠 **User Profiles** - Manage addresses and order history

### Advanced Features
- 🔍 **Real-time Search & Filtering** - Search books by title, author, category
- 🎟️ **Coupon System** - Apply discount codes to orders
- 📧 **Email Notifications** - Order confirmations and status updates
- 📄 **PDF Invoices** - Automatic invoice generation
- 🔐 **Admin Panel** - Comprehensive dashboard for store management
- 🌐 **Multi-language Support** - Internationalization ready
- 📊 **Analytics** - Order and sales tracking
- 💬 **Customer Support** - Support ticket system with file attachments

### Professional UI/UX
- 🎨 **Modern Design** - Professional Rokomari.com-style interface
- 📱 **Fully Responsive** - Works seamlessly on desktop, tablet, and mobile
- ⚡ **Real-time Updates** - Dynamic filtering without page reload
- 🔄 **Smooth Animations** - CSS transitions and hover effects
- 🎯 **Intuitive Navigation** - Mega menus and category browsing

## 📋 Requirements

### System Requirements
- Python 3.12.10 or higher
- MySQL 8.0 or higher
- Redis (for caching and Celery)
- pip (Python package manager)

### Python Dependencies
```
Django==4.2.7
djangorestframework==3.14.0
PyMySQL==1.1.0
Pillow==10.1.0
django-cors-headers==4.3.1
python-decouple==3.8
redis==5.0.1
django-redis==5.4.0
celery==5.3.4
django-crispy-forms==2.3
crispy-bootstrap5==2025.6
requests==2.31.0
django-filter==23.5
reportlab==4.0.7
openpyxl==3.1.2
django-ckeditor==6.7.0
xhtml2pdf==0.2.17
```

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/uzzalbhuiyan318/BookShop.git
cd BookShop
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=bookstore_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Site URL
SITE_URL=http://localhost:8000

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis Configuration (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Payment Gateway (SSLCommerz)
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
SSLCOMMERZ_BASE_URL=https://sandbox.sslcommerz.com  # Use for testing
```

### 5. Database Setup

#### Option A: Using MySQL Command Line
```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE bookstore_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Exit MySQL
EXIT;
```

#### Option B: Using MySQL Workbench
1. Open MySQL Workbench
2. Create new database named `bookstore_db`
3. Set character set to `utf8mb4`

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```
Follow the prompts to create your admin account:
- Username: admin
- Email: admin@example.com
- Password: (enter a strong password)

### 8. Load Static Files
```bash
python manage.py collectstatic --noinput
```

### 9. Create Sample Data (Optional)
```bash
# Run setup scripts to populate sample books and data
python setup_rentals.py
python create_sample_coupons.py
python create_test_addresses.py
```

## 🏃 Running the Application

### Start Development Server
```bash
python manage.py runserver
```

The application will be available at: `http://localhost:8000`

### Start with Custom Port
```bash
python manage.py runserver 8000
```

### Admin Panel Access
- URL: `http://localhost:8000/admin/`
- Username: `admin` (created during superuser setup)
- Password: (your superuser password)

### Run Celery (for async tasks like email sending)
```bash
# In a separate terminal
celery -A bookstore_project worker -l info
```

### Run Redis (if using caching)
```bash
# Start Redis server
redis-server
```

## 📁 Project Structure

```
BookShop/
├── accounts/                      # User authentication & profiles
│   ├── models.py                 # User models
│   ├── views.py                  # Auth views
│   ├── urls.py                   # Auth URLs
│   └── forms.py                  # Registration/Login forms
│
├── books/                         # Main book catalog
│   ├── models.py                 # Book model
│   ├── views.py                  # Book views
│   ├── api_views.py              # REST API views
│   ├── serializers.py            # API serializers
│   └── forms.py                  # Book forms
│
├── orders/                        # Order management
│   ├── models.py                 # Order models
│   ├── views.py                  # Order views
│   ├── email_utils.py            # Email notifications
│   ├── pdf_generator.py          # Invoice generation
│   └── tasks.py                  # Celery tasks
│
├── payments/                      # Payment processing
│   ├── models.py                 # Payment models
│   ├── sslcommerz.py             # SSLCommerz integration
│   └── views.py                  # Payment views
│
├── rentals/                       # Book rental system
│   ├── models.py                 # Rental models
│   └── views.py                  # Rental views
│
├── support/                       # Customer support
│   ├── models.py                 # Support ticket models
│   └── views.py                  # Support views
│
├── admin_panel/                   # Admin dashboard
│   ├── views.py                  # Dashboard views
│   └── models.py                 # Admin models
│
├── bookstore_project/             # Project configuration
│   ├── settings.py               # Django settings
│   ├── urls.py                   # URL configuration
│   ├── wsgi.py                   # WSGI config
│   └── celery.py                 # Celery config
│
├── static/                        # Static files
│   ├── css/
│   │   ├── style.css             # Main stylesheet
│   │   └── chat-widget.css       # Chat widget styles
│   ├── js/
│   │   ├── main.js               # Main JavaScript
│   │   └── chat-widget.js        # Chat widget script
│   └── images/                   # Static images
│
├── templates/                     # HTML templates
│   ├── base.html                 # Base template
│   ├── books/                    # Book templates
│   ├── orders/                   # Order templates
│   ├── accounts/                 # Account templates
│   └── ...                       # Other templates
│
├── media/                         # User-uploaded files
│   ├── books/
│   │   └── covers/               # Book covers
│   ├── profiles/                 # User profiles
│   └── support/                  # Support attachments
│
├── logs/                          # Application logs
│
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (create this)
├── db.sqlite3                     # SQLite database (development)
└── README.md                      # This file
```

## 🔧 Configuration

### Database Configuration
Edit `.env` to configure your MySQL database:
```env
DB_NAME=bookstore_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### Email Configuration
Set up email for order notifications:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password in `.env`

### Payment Gateway Setup
1. Create an account at [SSLCommerz](https://www.sslcommerz.com/)
2. Get your Store ID and Store Password
3. Add to `.env`:
```env
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
```

## 📚 Available URLs

### Public Pages
- `/` - Home page with featured books
- `/books/` - Book catalog
- `/books/<id>/` - Book detail page
- `/categories/` - Browse by category
- `/accounts/login/` - User login
- `/accounts/register/` - User registration
- `/orders/cart/` - Shopping cart
- `/orders/checkout/` - Checkout page
- `/rentals/` - Book rental page

### User Pages (Login Required)
- `/accounts/profile/` - User profile
- `/accounts/addresses/` - Manage addresses
- `/orders/history/` - Order history
- `/orders/<id>/invoice/` - Download invoice
- `/rentals/my-rentals/` - Active rentals
- `/support/` - Support tickets

### Admin Pages
- `/admin/` - Django admin panel
- `/admin-panel/` - Store dashboard
- `/admin-panel/books/` - Manage books
- `/admin-panel/orders/` - Manage orders
- `/admin-panel/users/` - Manage users

### API Endpoints
- `/api/books/` - Get all books (JSON)
- `/api/books/<id>/` - Get book detail (JSON)
- `/api/categories/` - Get categories (JSON)
- `/api/cart/add/` - Add to cart (API)
- `/api/cart/remove/` - Remove from cart (API)

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Run Specific Test
```bash
python manage.py test books.tests
```

### Test Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📧 Email Configuration

### Gmail Setup
1. Go to [Gmail App Passwords](https://myaccount.google.com/apppasswords)
2. Select Mail and Windows/Mac/Linux
3. Copy the generated 16-character password
4. Add to `.env`:
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
```

### Test Email
Run the test email script:
```bash
python test_email.py
```

## 🚀 Deployment

### Deploy to Production

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn bookstore_project.wsgi:application --bind 0.0.0.0:8000
```

#### Using Heroku
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create Procfile
echo "web: gunicorn bookstore_project.wsgi" > Procfile

# Deploy
git push heroku main
```

#### Using PythonAnywhere
1. Create account at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Upload your code
3. Configure virtual environment
4. Set up MySQL database
5. Configure WSGI file

### Environment Variables for Production
```env
DEBUG=False
SECRET_KEY=your-very-secure-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=production_db
DB_USER=prod_user
DB_PASSWORD=strong_password_here
SITE_URL=https://yourdomain.com
```

## 🐛 Troubleshooting

### Database Connection Error
```
Error: Can't connect to MySQL server
Solution:
1. Ensure MySQL is running: mysql.server start (macOS)
2. Check credentials in .env file
3. Verify database exists: CREATE DATABASE bookstore_db;
```

### Static Files Not Loading
```bash
python manage.py collectstatic --clear --noinput
```

### Migration Errors
```bash
# Reset migrations (development only)
python manage.py migrate books zero
python manage.py migrate
```

### Port Already in Use
```bash
# Use different port
python manage.py runserver 8001
```

### ModuleNotFoundError
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 📞 Support & Contact

### Report Issues
- GitHub Issues: [BookShop Issues](https://github.com/uzzalbhuiyan318/BookShop/issues)
- Email: uzzalbhuiyan318@gmail.com

### Developer
- **Name**: Uzzal Bhuiyan
- **GitHub**: [uzzalbhuiyan318](https://github.com/uzzalbhuiyan318)
- **Email**: uzzalbhuiyan318@gmail.com

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django Framework
- Bootstrap 5
- SSLCommerz Payment Gateway
- Font Awesome Icons
- All contributors and users

## 🔄 Version History

### Version 1.0.0 (Current)
- ✅ Complete book catalog with filtering
- ✅ Shopping cart and checkout
- ✅ Secure payment integration
- ✅ Book rental system
- ✅ User authentication and profiles
- ✅ Order management and invoices
- ✅ Customer support system
- ✅ Admin dashboard
- ✅ Professional UI/UX redesign
- ✅ Real-time search and filtering
- ✅ Multi-language support ready

## 🚧 Roadmap

- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] AI-powered book recommendations
- [ ] Social media integration
- [ ] Wishlist sharing
- [ ] Gift card system
- [ ] Subscription service
- [ ] Book review moderation system

## 💡 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**Made with ❤️ by Uzzal Bhuiyan**

**Last Updated**: November 17, 2025
