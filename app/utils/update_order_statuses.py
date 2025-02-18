from app import create_app, db
from app.models.order import Order

def update_order_statuses():
    """Update existing orders with correct order and payment statuses"""
    app = create_app()
    with app.app_context():
        # Get all orders
        orders = Order.query.all()
        
        for order in orders:
            # If order has a stripe_payment_id, it means payment was successful
            if order.stripe_payment_id:
                order.payment_status = 'paid'
                
                # If order was cancelled, check if it was refunded
                if order.status == 'cancelled':
                    if order.refund_id:
                        order.payment_status = 'refunded'
                    else:
                        # If cancelled but not refunded, mark for refund
                        order.payment_status = 'paid'
                elif order.status == 'paid':
                    # Convert 'paid' status to 'pending' for order status
                    order.status = 'pending'
            else:
                # No stripe payment ID means payment is pending
                order.payment_status = 'pending'
                
                # If no payment but status is 'paid', correct it
                if order.status == 'paid':
                    order.status = 'pending'
        
        # Commit all changes
        db.session.commit()
        print("Order statuses updated successfully!")

if __name__ == '__main__':
    update_order_statuses()
