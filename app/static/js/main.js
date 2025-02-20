// Cart functionality
function updateCartQuantity(itemId, quantity) {
    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cart count
            const cartTotal = document.getElementById('cart-total');
            if (cartTotal && data.cart_count !== undefined) {
                cartTotal.textContent = data.cart_count;
            }
            
            // Update item total if on cart page
            const itemTotal = document.querySelector(`.item-total[data-item-id="${itemId}"]`);
            if (itemTotal && data.item_total !== undefined) {
                itemTotal.textContent = `$${data.item_total.toFixed(2)}`;
            }
            
            // Update subtotal if on cart page
            const subtotalElement = document.getElementById('subtotal');
            if (subtotalElement && data.subtotal !== undefined) {
                subtotalElement.textContent = `$${data.subtotal.toFixed(2)}`;
            }
            
            // Update total if on cart page
            const totalElement = document.getElementById('total');
            if (totalElement && data.total !== undefined) {
                totalElement.textContent = `$${data.total.toFixed(2)}`;
            }
            
            showToast('Cart updated successfully', 'success');
        } else {
            showToast(data.message || 'Failed to update cart', 'error');
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
            // Update cart count using the updateCartCount function
            updateCartCount(data.cart_total);
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
                <button onclick="updateCartQuantity(${item.id}, 0)" class="btn-remove">Remove</button>
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
                    <button onclick="updateCartQuantity(${product.id}, 1)" class="btn-primary">Add to Cart</button>
                </div>
            </div>
        `).join('');
    }
}

// Update cart count in header
function updateCartCount(count) {
    const cartLink = document.querySelector('a[href*="/cart"]');
    if (!cartLink) return;

    let badge = document.getElementById('cart-total');
    
    if (count > 0) {
        if (!badge) {
            // Create new badge if it doesn't exist
            badge = document.createElement('span');
            badge.id = 'cart-total';
            badge.className = 'navbar-badge bg-danger';
            cartLink.appendChild(badge);
        }
        badge.textContent = count;
        badge.style.display = 'inline';
    } else if (badge) {
        // Hide badge when count is 0
        badge.style.display = 'none';
    }
}

// Update wishlist count in header
function updateWishlistCount(count) {
    const wishlistLink = document.querySelector('a[href*="wishlist"]');
    let wishlistTotal = document.getElementById('wishlist-total');
    
    if (count > 0) {
        if (!wishlistTotal) {
            wishlistTotal = document.createElement('span');
            wishlistTotal.className = 'navbar-badge bg-danger';
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

// Coupon functionality
function applyCoupon() {
    const couponInput = document.getElementById('couponCode');
    const applyButton = document.getElementById('applyCoupon');
    const buttonText = applyButton.querySelector('.button-text');
    const spinner = applyButton.querySelector('.spinner-border');
    const messageDiv = document.getElementById('couponMessage');
    
    // Rate limiting
    if (applyButton.dataset.lastClick && Date.now() - parseInt(applyButton.dataset.lastClick) < 2000) {
        showToast('Please wait a moment before trying again', 'warning');
        return;
    }
    applyButton.dataset.lastClick = Date.now();

    // Get coupon code
    const code = couponInput.value.trim();
    
    if (buttonText.textContent === 'Apply') {
        if (!code) {
            showInputError(couponInput, messageDiv, 'Please enter a coupon code');
            return;
        }
        
        // Show loading state
        setLoadingState(true, buttonText, spinner);
        
        fetch('/cart/coupons/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ code: code })
        })
        .then(response => response.json())
        .then(data => {
            setLoadingState(false, buttonText, spinner);
            
            if (data.success) {
                handleSuccessfulCoupon(data, couponInput, buttonText, messageDiv);
            } else {
                handleFailedCoupon(data, couponInput, messageDiv);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            setLoadingState(false, buttonText, spinner);
            showToast('An error occurred while applying the coupon', 'error');
        });
    } else {
        // Remove coupon
        setLoadingState(true, buttonText, spinner);
        
        fetch('/cart/coupons/remove', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            setLoadingState(false, buttonText, spinner);
            if (data.success) {
                handleCouponRemoval(couponInput, buttonText, messageDiv);
                updateOrderTotals(data);
            } else {
                showToast(data.error || 'Failed to remove coupon', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            setLoadingState(false, buttonText, spinner);
            showToast('An error occurred while removing the coupon', 'error');
        });
    }
}

function showInputError(input, messageDiv, message) {
    input.classList.add('is-invalid');
    messageDiv.className = 'form-text text-danger';
    messageDiv.textContent = message;
    setTimeout(() => input.classList.remove('is-invalid'), 3000);
}

function setLoadingState(loading, buttonText, spinner) {
    buttonText.style.opacity = loading ? '0' : '1';
    spinner.classList.toggle('d-none', !loading);
}

function handleSuccessfulCoupon(data, input, buttonText, messageDiv) {
    input.classList.add('is-valid');
    messageDiv.className = 'form-text text-success';
    messageDiv.textContent = data.message;
    buttonText.textContent = 'Remove';
    updateOrderTotals(data);
    
    // Add coupon details if provided
    if (data.coupon_details) {
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'coupon-details mt-2 small text-muted';
        detailsDiv.innerHTML = `
            ${data.coupon_details.valid_until ? `<div>Expires: ${data.coupon_details.valid_until}</div>` : ''}
            ${data.coupon_details.min_purchase ? `<div>Min. Purchase: $${data.coupon_details.min_purchase}</div>` : ''}
        `;
        messageDiv.parentNode.insertBefore(detailsDiv, messageDiv.nextSibling);
    }
}

function handleFailedCoupon(data, input, messageDiv) {
    input.classList.add('is-invalid');
    messageDiv.className = 'form-text text-danger';
    messageDiv.textContent = data.error;
    setTimeout(() => input.classList.remove('is-invalid'), 3000);
}

function handleCouponRemoval(input, buttonText, messageDiv) {
    input.value = '';
    input.classList.remove('is-valid', 'is-invalid');
    buttonText.textContent = 'Apply';
    messageDiv.className = 'form-text';
    messageDiv.textContent = '';
    
    // Remove coupon details if exists
    const detailsDiv = document.querySelector('.coupon-details');
    if (detailsDiv) {
        detailsDiv.remove();
    }
}

function updateOrderTotals(data) {
    const subtotalElement = document.getElementById('subtotal');
    const discountElement = document.getElementById('discount');
    const discountRow = document.getElementById('discount-row');
    const totalElement = document.getElementById('total');
    
    if (subtotalElement) subtotalElement.textContent = `$${data.subtotal.toFixed(2)}`;
    if (totalElement) totalElement.textContent = `$${data.total.toFixed(2)}`;
    
    if (data.discount > 0) {
        if (!discountRow) {
            const newDiscountRow = document.createElement('div');
            newDiscountRow.id = 'discount-row';
            newDiscountRow.className = 'd-flex justify-content-between mb-2';
            newDiscountRow.innerHTML = `
                <span>Discount:</span>
                <span id="discount">-$${data.discount.toFixed(2)}</span>
            `;
            totalElement.parentElement.parentElement.insertBefore(newDiscountRow, totalElement.parentElement);
        } else if (discountElement) {
            discountElement.textContent = `-$${data.discount.toFixed(2)}`;
        }
    } else if (discountRow) {
        discountRow.remove();
    }
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
            const itemId = e.target.dataset.itemId;
            if (itemId) {
                updateCartQuantity(itemId, e.target.value);
            }
        });
    });
    
    // Initialize counts when page loads
    if (document.querySelector('a[href*="cart"]')) {
        loadCounts();
    }
    
    // Setup coupon button
    const applyCouponBtn = document.getElementById('applyCoupon');
    if (applyCouponBtn) {
        applyCouponBtn.addEventListener('click', () => {
            if (applyCouponBtn.textContent.trim() === 'Apply') {
                applyCoupon();
            } else {
                removeCoupon();
            }
        });
    }
});

function removeCoupon() {
    fetch('/cart/coupons/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear coupon input
            document.getElementById('couponCode').value = '';
            
            // Update total
            document.getElementById('total').textContent = `$${data.new_total.toFixed(2)}`;
            
            // Remove discount row if it exists
            const discountRow = document.getElementById('discount-row');
            if (discountRow) {
                discountRow.remove();
            }
            
            // Update button text
            document.getElementById('applyCoupon').textContent = 'Apply';
            
            showToast(data.message, 'success');
        } else {
            showToast(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while removing the coupon', 'error');
    });
}
