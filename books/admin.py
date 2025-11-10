from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Category, Book, Review, Wishlist, Cart, Banner


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_bn', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_bn']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'price', 'discount_price', 'stock', 'is_active', 'is_featured']
    list_filter = ['category', 'language', 'is_active', 'is_featured', 'is_bestseller', 'created_at']
    search_fields = ['title', 'author', 'isbn', 'publisher']
    list_editable = ['is_active', 'stock']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'sales']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'publisher', 'isbn', 'category', 'language')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('Images', {
            'fields': ('cover_image', 'image2', 'image3')
        }),
        ('Details', {
            'fields': ('pages', 'publication_date', 'edition')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'is_bestseller')
        }),
        ('Metrics', {
            'fields': ('views', 'sales')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if obj.is_featured:
                featured_count = Book.objects.filter(is_featured=True).count()
                self.message_user(
                    request,
                    f'Book marked as featured. Total featured books: {featured_count}/4',
                    messages.SUCCESS
                )
        except ValidationError as e:
            self.message_user(request, str(e), messages.ERROR)
            raise


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['book__title', 'user__email', 'title', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__email', 'book__title']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'book', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'book__title', 'session_key']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle']
    list_editable = ['is_active', 'order']
