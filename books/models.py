from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from ckeditor.fields import RichTextField


class Category(models.Model):
    """Book Category Model"""
    
    name = models.CharField(max_length=200, unique=True, verbose_name='Category Name')
    name_bn = models.CharField(max_length=200, null=True, blank=True, verbose_name='Category Name (Bangla)')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Description')
    image = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name='Category Image')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    order = models.IntegerField(default=0, verbose_name='Display Order')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    """Book Model"""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('bn', 'Bangla'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=500, verbose_name='Book Title')
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    author = models.CharField(max_length=300, verbose_name='Author')
    publisher = models.CharField(max_length=300, null=True, blank=True, verbose_name='Publisher')
    isbn = models.CharField(max_length=13, unique=True, null=True, blank=True, verbose_name='ISBN')
    
    description = RichTextField(verbose_name='Description')
    short_description = models.TextField(max_length=500, blank=True, verbose_name='Short Description')
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en', verbose_name='Language')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price (BDT)')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Discount Price (BDT)')
    
    # Stock
    stock = models.IntegerField(default=0, verbose_name='Stock Quantity')
    
    # Images
    cover_image = models.ImageField(upload_to='books/covers/', verbose_name='Cover Image')
    image2 = models.ImageField(upload_to='books/', null=True, blank=True, verbose_name='Image 2')
    image3 = models.ImageField(upload_to='books/', null=True, blank=True, verbose_name='Image 3')
    
    # Book Details
    pages = models.IntegerField(null=True, blank=True, verbose_name='Number of Pages')
    publication_date = models.DateField(null=True, blank=True, verbose_name='Publication Date')
    edition = models.CharField(max_length=100, null=True, blank=True, verbose_name='Edition')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_featured = models.BooleanField(default=False, verbose_name='Featured')
    is_bestseller = models.BooleanField(default=False, verbose_name='Best Seller')
    
    # Metrics
    views = models.IntegerField(default=0, verbose_name='Views')
    sales = models.IntegerField(default=0, verbose_name='Total Sales')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price
    
    @property
    def discount_percentage(self):
        if self.discount_price and self.price > 0:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def total_reviews(self):
        return self.reviews.filter(is_approved=True).count()


class Review(models.Model):
    """Book Review Model"""
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating (1-5)'
    )
    title = models.CharField(max_length=200, verbose_name='Review Title')
    comment = models.TextField(verbose_name='Review Comment')
    is_approved = models.BooleanField(default=False, verbose_name='Approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['book', 'user']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.book.title} ({self.rating}★)"


class Wishlist(models.Model):
    """User Wishlist Model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ['-added_at']
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"{self.user.email} - {self.book.title}"


class Cart(models.Model):
    """Shopping Cart Model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart_items')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.email} - {self.book.title} (x{self.quantity})"
        return f"Guest - {self.book.title} (x{self.quantity})"
    
    @property
    def subtotal(self):
        return self.book.final_price * self.quantity


class Banner(models.Model):
    """Homepage Banner/Slider Model"""
    
    title = models.CharField(max_length=200, verbose_name='Title')
    subtitle = models.CharField(max_length=300, null=True, blank=True, verbose_name='Subtitle')
    image = models.ImageField(upload_to='banners/', verbose_name='Banner Image')
    link = models.URLField(null=True, blank=True, verbose_name='Link URL')
    button_text = models.CharField(max_length=50, null=True, blank=True, verbose_name='Button Text')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    order = models.IntegerField(default=0, verbose_name='Display Order')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
