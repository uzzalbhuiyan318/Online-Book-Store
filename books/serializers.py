"""
REST API Serializers
"""
from rest_framework import serializers
from books.models import Book, Category, Review
from orders.models import Order, OrderItem
from accounts.models import User, Address


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_bn', 'slug', 'description', 'image', 'is_active']


class BookListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'language',
            'price', 'discount_price', 'final_price', 'discount_percentage',
            'stock', 'is_in_stock', 'cover_image', 'is_featured', 'is_bestseller',
            'average_rating', 'total_reviews', 'created_at'
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    total_reviews = serializers.ReadOnlyField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'author', 'publisher', 'isbn',
            'description', 'short_description', 'category', 'language',
            'price', 'discount_price', 'final_price', 'discount_percentage',
            'stock', 'is_in_stock', 'cover_image', 'image2', 'image3',
            'pages', 'publication_date', 'edition',
            'is_active', 'is_featured', 'is_bestseller',
            'views', 'sales', 'average_rating', 'total_reviews',
            'created_at', 'updated_at'
        ]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'title', 'comment', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['book_title', 'book_author', 'quantity', 'price', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_number', 'status', 'payment_status', 'payment_method',
            'subtotal', 'shipping_cost', 'discount', 'total',
            'shipping_full_name', 'shipping_phone', 'shipping_address',
            'tracking_number', 'created_at', 'items'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'profile_image', 'date_joined']
        read_only_fields = ['date_joined']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'full_name', 'phone', 'email',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'is_default'
        ]
