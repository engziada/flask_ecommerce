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
        if (label && label.classList.contains('custom-file-label')) {
            const fileName = input.files[0]?.name || 'Choose file';
            // Remove any existing checkmark
            label.innerHTML = fileName;
        }

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
                
                // Remove the "current image will be kept" message if it exists
                const helpText = imageEntry.querySelector('.form-text.text-muted');
                if (helpText) {
                    helpText.remove();
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

    // Multiple Images Upload
    const multipleImagesInput = document.getElementById('multiple_images');
    const multipleImagesPreview = document.getElementById('multipleImagesPreview');
    
    if (multipleImagesInput) {
        multipleImagesInput.addEventListener('change', function() {
            // Clear preview
            multipleImagesPreview.innerHTML = '';
            
            if (this.files && this.files.length > 0) {
                // Show preview for each file
                Array.from(this.files).forEach((file, index) => {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const previewDiv = document.createElement('div');
                        previewDiv.classList.add('position-relative', 'mb-2');
                        
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.classList.add('img-thumbnail');
                        img.style.width = '100px';
                        img.style.height = '100px';
                        img.style.objectFit = 'contain';
                        img.alt = file.name;
                        
                        previewDiv.appendChild(img);
                        multipleImagesPreview.appendChild(previewDiv);
                    };
                    
                    reader.readAsDataURL(file);
                    
                    // Create image entries for each file
                    if (index === 0 && this.files.length > 0) {
                        // Don't add new entries yet - we'll do it when the form is submitted
                        // This prevents creating entries that might not be submitted
                    }
                });
                
                // Show message about number of images selected
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('alert', 'alert-info', 'mt-2');
                messageDiv.textContent = `${this.files.length} image(s) selected. They will be added when you submit the form.`;
                multipleImagesPreview.appendChild(messageDiv);
            }
        });
    }

    // Add new image entry
    if (addImageBtn) {
        addImageBtn.addEventListener('click', function() {
            addNewImageEntry();
        });
    }
    
    // Function to add a new image entry
    function addNewImageEntry() {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-4';
        
        const template = `
            <div class="card h-100 image-entry">
                <div class="card-body">
                    <div class="custom-file mb-2">
                        <input type="file" class="custom-file-input" name="images-${imageIndex}-image" id="images-${imageIndex}-image" accept="image/*">
                        <label class="custom-file-label" for="images-${imageIndex}-image">Choose file</label>
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" name="images-${imageIndex}-is_primary" id="images-${imageIndex}-is_primary">
                        <label class="form-check-label" for="images-${imageIndex}-is_primary">Primary Image</label>
                    </div>
                    <button type="button" class="btn btn-danger btn-sm mt-2 remove-image">
                        <i class="bi bi-trash"></i> Remove
                    </button>
                </div>
            </div>
        `;
        
        colDiv.innerHTML = template;
        imageContainer.appendChild(colDiv);
        imageIndex++;

        // Add event listener to new file input
        const newInput = colDiv.querySelector('.custom-file-input');
        newInput.addEventListener('change', function() {
            handleFileInput(this);
        });

        // Add event listener to new primary checkbox
        const newCheckbox = colDiv.querySelector('.form-check-input');
        newCheckbox.addEventListener('change', function() {
            if (this.checked) {
                document.querySelectorAll('.form-check-input[name$="is_primary"]').forEach(otherCheckbox => {
                    if (otherCheckbox !== this) {
                        otherCheckbox.checked = false;
                    }
                });
            }
        });
        
        return colDiv;
    }

    // Handle remove button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-image') || e.target.closest('.remove-image')) {
            const entry = e.target.closest('.image-entry');
            if (entry) {
                const col = entry.closest('.col-md-4');
                if (col) {
                    col.remove();
                } else {
                    entry.remove();
                }
            }
        }
    });

    // Form validation and submission
    const form = document.getElementById('productForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            // Process multiple images before submission
            const multipleImagesInput = document.getElementById('multiple_images');
            if (multipleImagesInput && multipleImagesInput.files && multipleImagesInput.files.length > 0) {
                // Create entries for each file in the multiple images input
                Array.from(multipleImagesInput.files).forEach((file, index) => {
                    const newEntry = addNewImageEntry();
                    
                    // Create a new FileList-like object containing just this file
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    
                    // Set the file to the input
                    const fileInput = newEntry.querySelector('input[type="file"]');
                    fileInput.files = dataTransfer.files;
                    
                    // Update the label
                    const label = newEntry.querySelector('.custom-file-label');
                    if (label) {
                        label.textContent = file.name;
                    }
                    
                    // Set the first image as primary if it's the only image
                    if (index === 0 && document.querySelectorAll('.image-entry').length === 1) {
                        const checkbox = newEntry.querySelector('.form-check-input');
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    }
                });
                
                // Clear the multiple images input to avoid duplicate uploads
                multipleImagesInput.value = '';
                multipleImagesPreview.innerHTML = '';
            }
            
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }
});
