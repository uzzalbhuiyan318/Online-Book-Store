import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from books.models import Book, Cart
from accounts.models import User

print("=== Cart State Check ===\n")

# Check active books
active_books = Book.objects.filter(is_active=True)
print(f"Active books: {active_books.count()}")
for book in active_books[:3]:
    print(f"  - ID: {book.id}, Title: {book.title}, Price: {book.price}")

# Check user
user = User.objects.filter(email='admin@gmail.com').first()
print(f"\nUser: {user} (email: {user.email if user else 'N/A'})")

# Check cart items
if user:
    carts = Cart.objects.filter(user=user)
    print(f"\nCart items for {user.email}: {carts.count()}")
    total = 0
    for cart in carts:
        print(f"  - {cart.book.title}: qty={cart.quantity}, subtotal={cart.subtotal}")
        total += cart.subtotal
    print(f"\nTotal: {total}")
else:
    print("\nNo user found!")

print("\n=== Session Cart Check ===")
# We can't check session cart without a request object
print("Session cart can only be checked in browser or with request object")
