import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from books.models import Book, Wishlist
from accounts.models import User

print("=== Wishlist Functionality Check ===\n")

# Check active books
active_books = Book.objects.filter(is_active=True)
print(f"Active books: {active_books.count()}")
if active_books.exists():
    print(f"First book: ID={active_books.first().id}, Title={active_books.first().title}")

# Check user
user = User.objects.filter(email='admin@gmail.com').first()
print(f"\nUser: {user} (email: {user.email if user else 'N/A'})")

# Check wishlist items
if user:
    wishlist_items = Wishlist.objects.filter(user=user)
    print(f"\nWishlist items for {user.email}: {wishlist_items.count()}")
    for item in wishlist_items:
        print(f"  - {item.book.title} (ID: {item.book.id})")
    
    # Get wishlist book IDs
    wishlist_book_ids = list(Wishlist.objects.filter(user=user).values_list('book_id', flat=True))
    print(f"\nWishlist book IDs: {wishlist_book_ids}")
else:
    print("\nNo user found!")

print("\n=== Check Complete ===")
