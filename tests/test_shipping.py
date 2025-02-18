from app import create_app
from app.utils.shipping import ShippingService, ShippingProvider

def test_shipping():
    app = create_app()
    with app.app_context():
        # Test destinations
        destinations = [
            {
                'city': 'Alexandria',
                'country': 'EG'
            },
            {
                'city': 'Dubai',
                'country': 'AE'
            }
        ]
        
        weights = [1.0, 2.5, 5.0]  # Test different weights
        
        for destination in destinations:
            print(f"\nTesting shipping to {destination['city']}, {destination['country']}")
            print("=" * 60)
            
            for weight in weights:
                print(f"\nPackage weight: {weight} KG")
                print("-" * 40)
                
                # Test standard shipping
                standard_service = ShippingService(ShippingProvider.ARAMEX_STANDARD)
                services = standard_service.get_available_services(destination, weight)
                print("Standard shipping:", services[0] if services else "No service available")
                
                # Test express shipping
                express_service = ShippingService(ShippingProvider.ARAMEX_EXPRESS)
                services = express_service.get_available_services(destination, weight)
                print("Express shipping:", services[0] if services else "No service available")

if __name__ == '__main__':
    test_shipping()
