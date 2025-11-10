// Custom JavaScript for BookStore

$(document).ready(function() {
    // Add to cart with AJAX
    $('.add-to-cart-form').on('submit', function(e) {
        e.preventDefault();
        
        const form = $(this);
        const url = form.attr('action');
        const data = form.serialize();
        
        $.ajax({
            type: 'POST',
            url: url,
            data: data,
            success: function(response) {
                // Update cart count
                if (response.cart_count) {
                    $('.cart-count').text(response.cart_count);
                }
                
                // Show success message
                showMessage('success', 'Book added to cart!');
            },
            error: function(xhr) {
                showMessage('error', 'Failed to add book to cart.');
            }
        });
    });
    
    // Update cart quantity
    $('.cart-quantity-input').on('change', function() {
        const input = $(this);
        const form = input.closest('form');
        form.submit();
    });
    
    // Add to wishlist
    $('.add-to-wishlist').on('click', function(e) {
        e.preventDefault();
        
        const button = $(this);
        const url = button.attr('href');
        
        $.ajax({
            type: 'POST',
            url: url,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                button.toggleClass('text-danger');
                showMessage('success', 'Wishlist updated!');
            },
            error: function(xhr) {
                if (xhr.status === 401) {
                    window.location.href = '/accounts/login/';
                } else {
                    showMessage('error', 'Failed to update wishlist.');
                }
            }
        });
    });
    
    // Confirm delete actions
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
        }
    });
    
    // Auto-hide dismissible alerts after 5 seconds (not static alerts)
    setTimeout(function() {
        $('.alert.alert-dismissible').fadeOut('slow');
    }, 5000);
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show message function
function showMessage(type, message) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const alert = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('.container').first().prepend(alert);
    
    setTimeout(function() {
        $('.alert').first().fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

// Image lazy loading
document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// Initialize tooltips
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Price range filter
$('#price-range').on('change', function() {
    const range = $(this).val().split('-');
    $('#min_price').val(range[0]);
    $('#max_price').val(range[1]);
    $(this).closest('form').submit();
});
