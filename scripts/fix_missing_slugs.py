import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
import django
django.setup()

from django.utils.text import slugify
from books.models import Book, Category
import django.db.models as models


def make_unique_slug(model, base_slug, instance_id=None):
    slug = base_slug
    counter = 1
    qs = model.objects
    while True:
        exists = qs.filter(slug=slug)
        if instance_id:
            exists = exists.exclude(pk=instance_id)
        if not exists.exists():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def slugify_unicode(value):
    try:
        return slugify(value, allow_unicode=True)
    except TypeError:
        return slugify(value)


def fix_categories():
    updated = 0
    for cat in Category.objects.filter(models.Q(slug__isnull=True) | models.Q(slug='')):
        base = slugify_unicode(cat.name or 'category')
        if not base:
            base = f"category-{cat.pk}"
        slug = make_unique_slug(Category, base, instance_id=cat.pk)
        cat.slug = slug
        cat.save()
        print(f"Updated Category {cat.pk} -> slug='{slug}'")
        updated += 1
    print(f"Categories updated: {updated}")


def fix_books():
    updated = 0
    for book in Book.objects.filter(models.Q(slug__isnull=True) | models.Q(slug='')):
        base = slugify_unicode(book.title or f'book-{book.pk}')
        if not base:
            base = f"book-{book.pk}"
        slug = make_unique_slug(Book, base, instance_id=book.pk)
        book.slug = slug
        book.save()
        print(f"Updated Book {book.pk} -> slug='{slug}'")
        updated += 1
    print(f"Books updated: {updated}")


if __name__ == '__main__':
    print('Fixing Category slugs...')
    fix_categories()
    print('Fixing Book slugs...')
    fix_books()
    print('Done')
