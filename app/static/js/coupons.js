// Coupon management functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const couponForm = document.getElementById('couponForm');
    const saveCouponBtn = document.getElementById('saveCouponBtn');
    const discountTypeSelect = document.getElementById('discountType');
    const couponModal = new bootstrap.Modal(document.getElementById('couponModal'));
    const modalTitle = document.getElementById('couponModalLabel');

    // Function to validate form data
    function validateCouponForm() {
        const code = document.getElementById('code').value.trim();
        const discountType = document.getElementById('discountType').value;
        const discountAmount = parseFloat(document.getElementById('discountAmount').value);
        const minPurchaseAmount = parseFloat(document.getElementById('minPurchaseAmount').value);
        const usageLimit = parseInt(document.getElementById('usageLimit').value);
        
        if (!code) {
            showToast('Error', 'Please enter a coupon code', 'error');
            return false;
        }
        
        if (discountType === 'percentage' && (discountAmount <= 0 || discountAmount > 100)) {
            showToast('Error', 'Percentage discount must be between 0 and 100', 'error');
            return false;
        }
        
        if (discountType === 'fixed' && discountAmount <= 0) {
            showToast('Error', 'Fixed discount amount must be greater than 0', 'error');
            return false;
        }
        
        if (minPurchaseAmount < 0) {
            showToast('Error', 'Minimum purchase amount cannot be negative', 'error');
            return false;
        }
        
        if (usageLimit < 1) {
            showToast('Error', 'Usage limit must be at least 1', 'error');
            return false;
        }
        
        return true;
    }

    // Function to reset form
    function resetForm() {
        couponForm.reset();
        document.getElementById('couponId').value = '';
        modalTitle.textContent = 'Create New Coupon';
        updateDiscountFields();
    }

    // Function to populate form with coupon data
    function populateForm(coupon) {
        document.getElementById('couponId').value = coupon.id;
        document.getElementById('code').value = coupon.code;
        document.getElementById('discountType').value = coupon.discount_type;
        document.getElementById('discountAmount').value = coupon.discount_amount;
        document.getElementById('minPurchaseAmount').value = coupon.min_purchase_amount;
        document.getElementById('maxDiscountAmount').value = coupon.max_discount_amount || '';
        document.getElementById('validFrom').value = coupon.valid_from ? coupon.valid_from.split('T')[0] : '';
        document.getElementById('validUntil').value = coupon.valid_until ? coupon.valid_until.split('T')[0] : '';
        document.getElementById('usageLimit').value = coupon.usage_limit || 1;
        updateDiscountFields();
        modalTitle.textContent = 'Edit Coupon';
    }
    
    // Function to submit coupon form data
    function submitCouponForm() {
        if (!validateCouponForm()) {
            return;
        }
        
        const couponId = document.getElementById('couponId').value;
        const formData = {
            code: document.getElementById('code').value.trim().toUpperCase(),
            discount_type: document.getElementById('discountType').value,
            discount_amount: parseFloat(document.getElementById('discountAmount').value),
            min_purchase_amount: parseFloat(document.getElementById('minPurchaseAmount').value),
            max_discount_amount: document.getElementById('maxDiscountAmount').value ? 
                parseFloat(document.getElementById('maxDiscountAmount').value) : null,
            valid_from: document.getElementById('validFrom').value || null,
            valid_until: document.getElementById('validUntil').value || null,
            usage_limit: parseInt(document.getElementById('usageLimit').value)
        };

        const url = couponId ? `/admin/api/coupons/${couponId}` : '/admin/api/coupons';
        const method = couponId ? 'PUT' : 'POST';
        
        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to save coupon');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showToast('Success', data.message || 'Coupon saved successfully', 'success');
                couponModal.hide();
                location.reload();
            } else {
                showToast('Error', data.error || 'Failed to save coupon', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error', error.message || 'An error occurred while saving the coupon', 'error');
        });
    }
    
    // Function to delete coupon
    function deleteCoupon(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const couponId = event.currentTarget.dataset.couponId;
        if (!confirm('Are you sure you want to delete this coupon?')) {
            return;
        }

        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        fetch(`/admin/api/coupons/${couponId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to delete coupon');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showToast('Success', data.message || 'Coupon deleted successfully', 'success');
                location.reload();
            } else {
                showToast('Error', data.error || 'Failed to delete coupon', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error', error.message || 'An error occurred while deleting the coupon', 'error');
        });
    }
    
    // Function to update discount fields based on type
    function updateDiscountFields() {
        const discountType = document.getElementById('discountType').value;
        const discountAmountGroup = document.querySelector('.discount-amount-group');
        const maxDiscountGroup = document.querySelector('.max-discount-group');
        const discountSymbol = document.querySelector('.discount-symbol');
        const discountHelp = document.querySelector('.discount-type-help');
        const discountInput = document.getElementById('discountAmount');
        
        // Reset validations
        discountInput.setAttribute('min', '0');
        discountInput.removeAttribute('max');
        
        switch(discountType) {
            case 'percentage':
                discountAmountGroup.style.display = 'block';
                maxDiscountGroup.style.display = 'block';
                discountSymbol.textContent = '%';
                discountHelp.textContent = 'Percentage discount off the cart total';
                discountInput.setAttribute('max', '100');
                discountInput.setAttribute('step', '0.1');
                if (parseFloat(discountInput.value) > 100) {
                    discountInput.value = '100';
                }
                break;
                
            case 'fixed':
                discountAmountGroup.style.display = 'block';
                maxDiscountGroup.style.display = 'none';
                discountSymbol.textContent = 'EGP';
                discountHelp.textContent = 'Fixed amount discount off the cart total';
                discountInput.setAttribute('step', '0.01');
                break;
                
            case 'free_shipping':
                discountAmountGroup.style.display = 'none';
                maxDiscountGroup.style.display = 'none';
                discountHelp.textContent = 'Free shipping on the entire order';
                discountInput.value = '0';
                break;
        }
    }

    // Event listeners
    if (saveCouponBtn) {
        saveCouponBtn.addEventListener('click', submitCouponForm);
    }

    if (discountTypeSelect) {
        discountTypeSelect.addEventListener('change', updateDiscountFields);
        // Initialize fields
        updateDiscountFields();
    }

    // Event listener for edit buttons
    document.querySelectorAll('.edit-coupon-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            const couponId = this.dataset.couponId;
            const couponData = JSON.parse(document.getElementById(`coupon-${couponId}`).value);
            populateForm(couponData);
            couponModal.show();
        });
    });

    // Event listener for delete buttons
    document.querySelectorAll('.delete-coupon-btn').forEach(button => {
        button.addEventListener('click', deleteCoupon);
    });

    // Event listener for modal hidden event
    document.getElementById('couponModal').addEventListener('hidden.bs.modal', function () {
        resetForm();
    });
});
