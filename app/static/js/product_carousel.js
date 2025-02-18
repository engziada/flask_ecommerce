document.addEventListener('DOMContentLoaded', function() {
    // Handle thumbnail clicks
    document.querySelectorAll('.thumbnail-image').forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            // Remove active class from all thumbnails
            document.querySelectorAll('.thumbnail-image').forEach(thumb => {
                thumb.classList.remove('active');
            });
            
            // Add active class to clicked thumbnail
            this.classList.add('active');
        });
    });

    // Update thumbnail active state when carousel slides
    const productCarousel = document.getElementById('productImageCarousel');
    if (productCarousel) {
        productCarousel.addEventListener('slid.bs.carousel', function(event) {
            // Remove active class from all thumbnails
            document.querySelectorAll('.thumbnail-image').forEach(thumb => {
                thumb.classList.remove('active');
            });
            
            // Add active class to current slide's thumbnail
            const activeIndex = event.to;
            const activeThumbnail = document.querySelector(`.thumbnail-image[data-bs-slide-to="${activeIndex}"]`);
            if (activeThumbnail) {
                activeThumbnail.classList.add('active');
            }
        });
    }

    // Pause product card carousels on hover
    document.querySelectorAll('.product-card .carousel').forEach(carousel => {
        carousel.addEventListener('mouseenter', function() {
            bootstrap.Carousel.getInstance(this).pause();
        });
        
        carousel.addEventListener('mouseleave', function() {
            bootstrap.Carousel.getInstance(this).cycle();
        });
    });
});
