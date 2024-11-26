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

// Initialize image preview handlers
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.querySelector('input[type="file"][accept="image/*"]');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            handleImagePreview(this);
        });
    }

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
});
