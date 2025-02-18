document.addEventListener('DOMContentLoaded', function() {
    // Handle primary image checkboxes
    document.querySelectorAll('.form-check-input[name$="is_primary"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                // Uncheck all other primary checkboxes
                document.querySelectorAll('.form-check-input[name$="is_primary"]').forEach(otherCheckbox => {
                    if (otherCheckbox !== this) {
                        otherCheckbox.checked = false;
                    }
                });
            } else {
                // Ensure at least one image is primary
                const anyPrimaryChecked = Array.from(
                    document.querySelectorAll('.form-check-input[name$="is_primary"]')
                ).some(cb => cb.checked);
                
                if (!anyPrimaryChecked) {
                    // If no primary is selected, select the first one
                    const firstCheckbox = document.querySelector('.form-check-input[name$="is_primary"]');
                    if (firstCheckbox) {
                        firstCheckbox.checked = true;
                    }
                }
            }
        });
    });

    // Image handling
    const imageContainer = document.getElementById('image-container');
    const addImageBtn = document.getElementById('add-image');
    const imageCount = document.querySelectorAll('.image-entry').length;
    let imageIndex = imageCount;

    // Handle file input change
    function handleFileInput(input) {
        // Update label with filename
        const label = input.nextElementSibling;
        const fileName = input.files[0]?.name || 'Choose file';
        label.textContent = fileName;

        // Preview image
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            const imageEntry = input.closest('.image-entry');
            
            reader.onload = function(e) {
                // Find existing preview
                const existingPreview = imageEntry.querySelector('.preview-image');
                
                // Create new preview
                const img = document.createElement('img');
                img.src = e.target.result;
                img.classList.add('img-fluid', 'mb-2', 'preview-image');
                img.alt = 'Product Image';
                
                // Replace existing preview if it exists, otherwise insert new one
                if (existingPreview) {
                    existingPreview.replaceWith(img);
                } else {
                    imageEntry.querySelector('.card-body').insertBefore(img, imageEntry.querySelector('.custom-file'));
                }
                
                // Remove any existing hidden input for this image entry
                const existingHidden = imageEntry.querySelector('input[name^="existing_images-"]');
                if (existingHidden) {
                    existingHidden.remove();
                }
            };
            
            reader.readAsDataURL(input.files[0]);
        }
    }

    document.querySelectorAll('.custom-file-input').forEach(input => {
        input.addEventListener('change', function() {
            handleFileInput(this);
        });
    });

    // Add new image entry
    if (addImageBtn) {
        addImageBtn.addEventListener('click', function() {
            const template = `
                <div class="card mb-3 image-entry">
                    <div class="card-body">
                        <div class="custom-file mb-2">
                            <input type="file" class="custom-file-input" name="images-${imageIndex}-image" accept="image/*">
                            <label class="custom-file-label">Choose file</label>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" name="images-${imageIndex}-is_primary" id="images-${imageIndex}-is_primary">
                            <label class="form-check-label" for="images-${imageIndex}-is_primary">Primary Image</label>
                        </div>
                        <button type="button" class="btn btn-danger mt-2 remove-image">Remove</button>
                    </div>
                </div>
            `;
            imageContainer.insertAdjacentHTML('beforeend', template);
            imageIndex++;

            // Add event listener to new file input
            const newInput = imageContainer.lastElementChild.querySelector('.custom-file-input');
            newInput.addEventListener('change', function() {
                handleFileInput(this);
            });

            // Add event listener to new primary checkbox
            const newCheckbox = imageContainer.lastElementChild.querySelector('.form-check-input');
            newCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    document.querySelectorAll('.form-check-input[name$="is_primary"]').forEach(otherCheckbox => {
                        if (otherCheckbox !== this) {
                            otherCheckbox.checked = false;
                        }
                    });
                }
            });
        });
    }

    // Handle remove button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-image')) {
            e.target.closest('.image-entry').remove();
        }
    });

    // Form validation
    const form = document.getElementById('productForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }
});
