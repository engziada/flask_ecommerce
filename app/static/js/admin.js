// Image Preview
function handleImagePreview(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const previewContainer = document.getElementById('image-preview');
            if (!previewContainer) {
                const container = document.createElement('div');
                container.id = 'image-preview';
                container.className = 'mt-2';
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'admin-form preview-image';
                container.appendChild(img);
                input.parentNode.appendChild(container);
            } else {
                const img = previewContainer.querySelector('img');
                img.src = e.target.result;
            }
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Handle multiple image previews
function handleMultipleImagePreviews(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        const imageEntry = input.closest('.image-entry');
        
        reader.onload = function(e) {
            let previewContainer = imageEntry.querySelector('.image-preview');
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.className = 'image-preview mt-2';
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'img-thumbnail';
                img.style.maxHeight = '150px';
                previewContainer.appendChild(img);
                imageEntry.querySelector('.col-md-8').appendChild(previewContainer);
            } else {
                const img = previewContainer.querySelector('img');
                img.src = e.target.result;
            }
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Handle color preview
function handleColorPreview(input) {
    const colorEntry = input.closest('.color-entry');
    let previewBox = colorEntry.querySelector('.color-preview');
    if (!previewBox) {
        previewBox = document.createElement('div');
        previewBox.className = 'color-preview';
        input.parentNode.insertBefore(previewBox, input);
    }
    previewBox.style.backgroundColor = input.value;
}

// Coupon Management Functions
window.editCoupon = function(coupon) {
    // Populate modal fields with coupon data
    document.getElementById('couponId').value = coupon.id;
    document.getElementById('code').value = coupon.code;
    document.getElementById('discountType').value = coupon.discount_type;
    document.getElementById('discountAmount').value = coupon.discount_amount;
    document.getElementById('minPurchaseAmount').value = coupon.min_purchase_amount;
    document.getElementById('maxDiscountAmount').value = coupon.max_discount_amount || '';
    document.getElementById('validFrom').value = coupon.valid_from ? coupon.valid_from.split('T')[0] : '';
    document.getElementById('validUntil').value = coupon.valid_until ? coupon.valid_until.split('T')[0] : '';
    document.getElementById('usageLimit').value = coupon.usage_limit || '';
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('couponModal'));
    modal.show();
}

window.deleteCoupon = function(couponId) {
    if (confirm('Are you sure you want to delete this coupon?')) {
        fetch(`/admin/coupons/${couponId}/delete`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the row from the table
                const row = document.querySelector(`tr[data-coupon-id="${couponId}"]`);
                if (row) row.remove();
                showToast('Success', 'Coupon deleted successfully', 'success');
            } else {
                showToast('Error', data.message || 'Failed to delete coupon', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error', 'Failed to delete coupon', 'error');
        });
    }
}

// Toast notification function
function showToast(title, message, type = 'info') {
    const event = new CustomEvent('flash-message', {
        detail: { message, category: type }
    });
    window.dispatchEvent(event);
}

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    // Initialize image preview handlers
    const imageInput = document.querySelector('input[type="file"][accept="image/*"]');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            handleImagePreview(this);
        });
    }

    // Initialize multiple image preview handlers
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[type="file"][accept="image/*"]')) {
            handleMultipleImagePreviews(e.target);
        }
        if (e.target.matches('input[type="color"]')) {
            handleColorPreview(e.target);
        }
    });

    // Handle primary image radio buttons
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name$="-is_primary"]')) {
            const allPrimaryCheckboxes = document.querySelectorAll('input[name$="-is_primary"]');
            allPrimaryCheckboxes.forEach(checkbox => {
                if (checkbox !== e.target) {
                    checkbox.checked = false;
                }
            });
        }
    });

    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Initialize status badge colors
    const statusBadges = document.querySelectorAll('.status-badge');
    statusBadges.forEach(badge => {
        const status = badge.dataset.status;
        badge.classList.add(`status-${status.toLowerCase()}`);
    });

    // Handle delete confirmations
    const deleteButtons = document.querySelectorAll('[data-delete-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Handle form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Handle form submission
    const form = document.getElementById('couponForm');
    const saveButton = document.getElementById('saveCoupon');
    
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const formData = new FormData(form);
            const couponId = document.getElementById('couponId').value;
            const url = couponId ? `/admin/coupons/${couponId}/edit` : '/admin/coupons/create';
            
            fetch(url, {
                method: couponId ? 'PUT' : 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close modal and refresh page
                    bootstrap.Modal.getInstance(document.getElementById('couponModal')).hide();
                    location.reload();
                } else {
                    showToast('Error', data.message || 'Failed to save coupon', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error', 'Failed to save coupon', 'error');
            });
        });
    }

    // Handle discount type changes
    const discountTypeSelect = document.getElementById('discountType');
    if (discountTypeSelect) {
        discountTypeSelect.addEventListener('change', function() {
            const amountGroup = document.querySelector('.discount-amount-group');
            const symbol = document.querySelector('.discount-symbol');
            const amountInput = document.getElementById('discountAmount');
            
            if (this.value === 'percentage') {
                symbol.textContent = '%';
                amountInput.max = '100';
                amountGroup.style.display = 'block';
            } else if (this.value === 'fixed') {
                symbol.textContent = '$';
                amountInput.removeAttribute('max');
                amountGroup.style.display = 'block';
            } else {
                amountGroup.style.display = 'none';
            }
        });
    }

    // Reset form when modal is closed
    const couponModal = document.getElementById('couponModal');
    if (couponModal) {
        couponModal.addEventListener('hidden.bs.modal', function () {
            form.reset();
            document.getElementById('couponId').value = '';
        });
    }

    // Handle coupon edit and delete buttons using event delegation
    const couponsTable = document.getElementById('couponsTable');
    if (couponsTable) {
        couponsTable.addEventListener('click', function(e) {
            const editButton = e.target.closest('[data-coupon]');
            const deleteButton = e.target.closest('[data-coupon-id]');

            if (editButton) {
                const coupon = JSON.parse(editButton.dataset.coupon);
                editCoupon(coupon);
            } else if (deleteButton) {
                const couponId = deleteButton.dataset.couponId;
                deleteCoupon(couponId);
            }
        });
    }

    // Initialize color previews for existing colors
    document.querySelectorAll('input[type="color"]').forEach(input => {
        handleColorPreview(input);
    });
});
