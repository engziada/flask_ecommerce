from flask import jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.reviews import bp
from app.models.review import Review
from app.models.product import Product
from app.extensions import db

@bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    """Add a review for a product"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user already reviewed this product
    existing_review = Review.query.filter_by(
        product_id=product_id,
        user_id=current_user.id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this product', 'warning')
        return redirect(url_for('shop.product_detail', product_id=product_id))
    
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating between 1 and 5', 'danger')
        return redirect(url_for('shop.product_detail', product_id=product_id))
    
    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=rating,
        comment=comment
    )
    
    db.session.add(review)
    db.session.commit()
    
    flash('Thank you for your review!', 'success')
    return redirect(url_for('shop.product_detail', product_id=product_id))

@bp.route('/product/<int:product_id>/reviews')
def get_reviews(product_id):
    """Get all reviews for a product"""
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    reviews = Review.query.filter_by(product_id=product_id)\
        .order_by(Review.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    reviews_dict = {
        'items': [review.to_dict() for review in reviews.items],
        'total': reviews.total,
        'pages': reviews.pages,
        'current_page': reviews.page
    }
    
    return jsonify(reviews_dict)

@bp.route('/review/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    """Delete a review"""
    review = Review.query.get_or_404(review_id)
    
    if review.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'message': 'Review deleted successfully'})
