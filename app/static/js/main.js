// Cart functionality
function updateCart(productId, quantity) {
    fetch('/cart/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartUI(data.cart_total, data.cart_items);
            showToast('Cart updated successfully', 'success');
        } else {
            showToast('Failed to update cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

// Function to add items to the cart
function addToCart(productId) {
    fetch(`/cart/add/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cart total badge
            const cartTotalBadge = document.getElementById('cart-total');
            if (cartTotalBadge) {
                cartTotalBadge.textContent = data.cart_total;
            } else {
                // If badge doesn't exist, create it
                const cartLink = document.querySelector('a[href*="/cart"]');
                if (cartLink) {
                    const badge = document.createElement('span');
                    badge.id = 'cart-total';
                    badge.className = 'badge bg-danger';
                    badge.textContent = data.cart_total;
                    cartLink.appendChild(badge);
                }
            }
            showToast('Product added to cart successfully', 'success');
        } else {
            showToast(data.message || 'Failed to add product to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while adding to cart', 'error');
    });
}

// Function to remove items from cart
function removeFromCart(itemId) {
    if (!confirm('Are you sure you want to remove this item from your cart?')) {
        return;
    }

    fetch(`/cart/remove/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove the item from UI
            const itemElement = document.querySelector(`[data-cart-item="${itemId}"]`);
            if (itemElement) {
                itemElement.remove();
            }
            updateCartCount(data.cart_total);
            showToast('Product removed from cart', 'success');
        } else {
            showToast(data.message || 'Failed to remove item from cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while removing from cart', 'error');
    });
}

// Wishlist functionality
function toggleWishlist(productId) {
    fetch(`/wishlist/toggle/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update wishlist icon
            const wishlistIcon = document.querySelector(`[data-wishlist-product="${productId}"] i`);
            if (wishlistIcon) {
                wishlistIcon.classList.toggle('text-danger');
                wishlistIcon.classList.toggle('bi-heart');
                wishlistIcon.classList.toggle('bi-heart-fill');
            }
            
            // Update wishlist count
            updateWishlistCount(data.wishlist_total);
            
            // Show appropriate message
            if (data.action === 'added') {
                showToast('Product added to wishlist', 'success');
            } else {
                showToast('Product removed from wishlist', 'success');
            }
        } else {
            showToast(data.message || 'Failed to update wishlist', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while updating wishlist', 'error');
    });
}

// Product search
function searchProducts(query) {
    fetch(`/search?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
        updateProductList(data.products);
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Search failed', 'error');
    });
}

// UI Updates
function updateCartUI(total, items) {
    const cartTotal = document.getElementById('cart-total');
    const cartItems = document.getElementById('cart-items');
    
    if (cartTotal) cartTotal.textContent = `$${total.toFixed(2)}`;
    if (cartItems) {
        cartItems.innerHTML = items.map(item => `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.name}" class="cart-item-image">
                <div class="cart-item-details">
                    <h3>${item.name}</h3>
                    <p>$${item.price} x ${item.quantity}</p>
                </div>
                <button onclick="updateCart(${item.id}, 0)" class="btn-remove">Remove</button>
            </div>
        `).join('');
    }
}

function updateWishlistUI(productId, inWishlist) {
    const wishlistBtn = document.querySelector(`[data-wishlist-id="${productId}"]`);
    if (wishlistBtn) {
        wishlistBtn.classList.toggle('in-wishlist', inWishlist);
        wishlistBtn.setAttribute('aria-pressed', inWishlist);
    }
}

function updateProductList(products) {
    const productList = document.getElementById('product-list');
    if (productList) {
        productList.innerHTML = products.map(product => `
            <div class="product-card">
                <img src="${product.image}" alt="${product.name}" class="product-image">
                <div class="product-details">
                    <h3>${product.name}</h3>
                    <p>${product.description}</p>
                    <p class="price">$${product.price}</p>
                    <button onclick="updateCart(${product.id}, 1)" class="btn-primary">Add to Cart</button>
                </div>
            </div>
        `).join('');
    }
}

// Update cart count in header
function updateCartCount(count) {
    const cartLink = document.querySelector('a[href*="cart"]');
    let cartTotal = document.getElementById('cart-total');
    
    if (count > 0) {
        if (!cartTotal) {
            cartTotal = document.createElement('span');
            cartTotal.className = 'badge bg-danger';
            cartTotal.id = 'cart-total';
            cartLink.appendChild(cartTotal);
        }
        cartTotal.textContent = count;
    } else if (cartTotal) {
        cartTotal.remove();
    }
}

// Update wishlist count in header
function updateWishlistCount(count) {
    const wishlistLink = document.querySelector('a[href*="wishlist"]');
    let wishlistTotal = document.getElementById('wishlist-total');
    
    if (count > 0) {
        if (!wishlistTotal) {
            wishlistTotal = document.createElement('span');
            wishlistTotal.className = 'badge bg-danger';
            wishlistTotal.id = 'wishlist-total';
            wishlistLink.appendChild(wishlistTotal);
        }
        wishlistTotal.textContent = count;
    } else if (wishlistTotal) {
        wishlistTotal.remove();
    }
}

// Load counts from server
function loadCounts() {
    fetch('/api/counts')
        .then(response => response.json())
        .then(data => {
            if (data.cart_count !== undefined) {
                updateCartCount(data.cart_count);
            }
            if (data.wishlist_count !== undefined) {
                updateWishlistCount(data.wishlist_count);
            }
        })
        .catch(error => console.error('Error loading counts:', error));
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast show custom-toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    const titles = {
        success: 'Success!',
        error: 'Error!',
        warning: 'Warning!',
        info: 'Information'
    };

    toast.innerHTML = `
        <div class="toast-header">
            <i class="${icons[type]} toast-icon me-2"></i>
            <strong class="me-auto">${titles[type]}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    toastContainer.appendChild(toast);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);

    // Close button functionality
    const closeBtn = toast.querySelector('.btn-close');
    closeBtn.addEventListener('click', () => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
        }, 300);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Setup search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let timeout = null;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => searchProducts(e.target.value), 300);
        });
    }
    
    // Setup quantity inputs
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', (e) => {
            const productId = e.target.dataset.productId;
            updateCart(productId, e.target.value);
        });
    });
    
    // Initialize counts when page loads
    if (document.querySelector('a[href*="cart"]')) {
        loadCounts();
    }
});
