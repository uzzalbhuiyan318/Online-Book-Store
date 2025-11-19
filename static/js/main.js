// Custom JavaScript for BookStore

$(document).ready(function() {
    console.log('Main.js loaded and ready');
    console.log('jQuery version:', $.fn.jquery);
    console.log('Mega dropdowns found:', $('.mega-dropdown').length);
    
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
                    $('.cart-count').text(response.cart_count).show();
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

// Mega Menu Hover Functionality - Simple and Direct
console.log('Setting up mega menu hover');

// Remove any conflicting Bootstrap dropdown behavior
$('.mega-dropdown .dropdown-toggle').on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('Dropdown toggle clicked - prevented default');
});

// Simple hover with mouseenter and mouseleave
$('.mega-dropdown').on('mouseenter', function() {
    console.log('Mouse entered mega dropdown');
    $(this).addClass('show');
    $(this).find('.mega-menu').addClass('show');
}).on('mouseleave', function() {
    console.log('Mouse left mega dropdown');
    $(this).removeClass('show');
    $(this).find('.mega-menu').removeClass('show');
});

// Prevent menu from closing when clicking inside
$('.mega-menu').on('click', function(e) {
    e.stopPropagation();
});

console.log('Mega menu setup complete');

// ========== Real-Time Page Search/Filter ==========
const searchInput = $('#searchInput');
let searchTimeout = null;

// Only enable on pages with book cards
if ($('.book-card, .card').length > 0) {
    searchInput.on('input', function() {
        const query = $(this).val().trim().toLowerCase();
        
        // Clear previous timeout
        clearTimeout(searchTimeout);
        
        // Debounce - wait 200ms after user stops typing
        searchTimeout = setTimeout(function() {
            filterBooksOnPage(query);
        }, 200);
    });
}

function filterBooksOnPage(query) {
    // Get all book cards
    const bookCards = $('.card');
    let visibleCount = 0;
    
    if (!query || query.length === 0) {
        // Show all books if search is empty
        bookCards.closest('.col-md-3, .col-md-4, .col-sm-6').show();
        updateSearchStatus(bookCards.length, bookCards.length);
        return;
    }
    
    // Filter books
    bookCards.each(function() {
        const card = $(this);
        const cardContainer = card.closest('.col-md-3, .col-md-4, .col-sm-6');
        
        // Get text content from the card
        const title = card.find('.card-title').text().toLowerCase();
        const author = card.find('.card-text.text-muted').first().text().toLowerCase();
        const allText = card.text().toLowerCase();
        
        // Check if query matches title, author, or any text in the card
        if (title.includes(query) || author.includes(query) || allText.includes(query)) {
            cardContainer.show();
            
            // Highlight matching text (optional)
            highlightCardText(card, query);
            visibleCount++;
        } else {
            cardContainer.hide();
        }
    });
    
    // Update search status
    updateSearchStatus(visibleCount, bookCards.length);
}

function highlightCardText(card, query) {
    // Add a subtle highlight effect to visible cards
    card.addClass('search-highlight');
    setTimeout(function() {
        card.removeClass('search-highlight');
    }, 300);
}

function updateSearchStatus(visibleCount, totalCount) {
    // Remove existing search status
    $('#searchStatus').remove();
    // Alert removed - no status message shown while filtering
}

// Clear search when clicking the search clear button (if present)
searchInput.on('search', function() {
    if (this.value === '') {
        filterBooksOnPage('');
    }
});

// Prevent form submission if on a page with books (for filtering)
// Allow submission on other pages
if ($('.book-card, .card').length > 0) {
    $('#searchForm').on('submit', function(e) {
        const query = searchInput.val().trim();
        // If already on a book page and has results, prevent submission
        if (query && $('.card:visible').length > 0) {
            e.preventDefault();
            filterBooksOnPage(query.toLowerCase());
        }
        // Otherwise allow normal form submission to search page
    });
}
