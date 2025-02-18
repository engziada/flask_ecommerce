from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.category import Category
from app.extensions import db
from app.shop import bp

@bp.route('/')
def index():
    """Shop index page"""
    page = request.args.get('page', 1, type=int)
    products = Product.query.filter_by(is_active=True).paginate(
        page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
    )
    categories = Category.query.all()
    return render_template('shop/index.html', products=products, categories=categories)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    return render_template('shop/product_detail.html', product=product)

@bp.route('/category/<int:category_id>')
def category_products(category_id):
    """Category products page"""
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    products = Product.query.filter_by(category_id=category_id, is_active=True).paginate(
        page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
    )
    return render_template('shop/category.html', category=category, products=products)

@bp.route('/search')
def search():
    """Search products"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if query:
        products = Product.query.filter(
            Product.name.ilike(f'%{query}%') | 
            Product.description.ilike(f'%{query}%')
        ).filter_by(is_active=True).paginate(
            page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
        )
    else:
        products = Product.query.filter_by(is_active=True).paginate(
            page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
        )
    
    return render_template('shop/search.html', products=products, query=query)
