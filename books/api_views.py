"""
REST API Views
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Book, Category, Review
from orders.models import Order
from .serializers import (
    BookListSerializer, BookDetailSerializer,
    CategorySerializer, ReviewSerializer, OrderSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for categories
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for books
    """
    queryset = Book.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'language', 'is_featured', 'is_bestseller']
    search_fields = ['title', 'author', 'isbn', 'publisher']
    ordering_fields = ['price', 'created_at', 'views', 'sales']
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured books"""
        books = self.queryset.filter(is_featured=True)[:8]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        """Get bestseller books"""
        books = self.queryset.filter(is_bestseller=True)[:8]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        """Get new arrival books"""
        books = self.queryset.order_by('-created_at')[:8]
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for reviews
    """
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['book', 'rating']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for orders (user's own orders only)
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        if not order.can_be_cancelled():
            return Response(
                {'error': 'This order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        return Response({'message': 'Order cancelled successfully'})
