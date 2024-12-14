import unittest
import cloudscraper
import json
import sys
from app.utils.shipping import ShippingProvider, ShippingService

# Set console encoding to UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class TestEgyPostShipping(unittest.TestCase):
    def setUp(self):
        self.url = "https://egyptpost.gov.eg/ar-EG/CalculatePostage/CalculatePostalFees"
        # Create a scraper instance
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Additional headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Origin": "https://egyptpost.gov.eg",
            "Referer": "https://egyptpost.gov.eg/ar-EG/CalculatePostage"
        }
        
        # Initialize session
        try:
            self.scraper.get(
                "https://egyptpost.gov.eg/ar-EG/CalculatePostage",
                headers=self.headers
            )
        except Exception as e:
            print(f"Setup error: {str(e)}")

    def safe_print_response(self, response_text):
        """Safely print response text that may contain non-ASCII characters"""
        try:
            # Try to parse as JSON first
            data = json.loads(response_text)
            print("Response:", json.dumps(data, ensure_ascii=False))
        except:
            # If not JSON, print raw text
            try:
                print("Response:", response_text.encode('utf-8').decode('utf-8'))
            except:
                print("Response: Unable to decode response text")

    def test_local_shipping_calculation(self):
        """Test local shipping calculation with EgyPost"""
        payload = {
            "shippingType": "Local",
            "serviceType": "EB",
            "originGovernorateId": 1,        # Cairo
            "destinationGovernorateId": 12,   # Alexandria
            "isCod": 1,
            "weightInGrams": "1000",
            "destinationCountryId": 0
        }

        try:
            response = self.scraper.post(
                self.url,
                json=payload,
                headers=self.headers
            )
            
            print("\nTest Results:")
            print(f"Status Code: {response.status_code}")
            print("Response Headers:", dict(response.headers))
            
            if response.status_code == 200:
                self.safe_print_response(response.text)
                data = response.json()
                
                # Check if response has data array
                self.assertTrue('data' in data and isinstance(data['data'], list), 
                              "Response should contain data array")
                
                # Check if we have shipping services
                self.assertTrue(len(data['data']) > 0, 
                              "Response should contain at least one shipping service")
                
                # Check if first service has a price
                first_service = data['data'][0]
                self.assertTrue('servicePrice' in first_service and isinstance(first_service['servicePrice'], (int, float)), 
                              "Service should have a valid price")
                
                # Print shipping options
                print("\nAvailable Shipping Services:")
                for service in data['data']:
                    print(f"- {service['serviceName']}: {service['servicePrice']} EGP")
                    print(f"  Delivery Time: {service['periodInDays']} days")
                    print(f"  Max Weight: {service['maxWeight']} grams")
                    print("  Features:")
                    for feature in service['features']:
                        print(f"    * {feature}")
                    print()
            else:
                print("\nError Response:")
                self.safe_print_response(response.text)
            
        except Exception as e:
            print(f"Request failed: {str(e)}")
            raise

    def test_different_weights(self):
        """Test shipping calculation with different weights"""
        weights = [500, 1000, 2000, 5000]  # weights in grams
        
        for weight in weights:
            payload = {
                "shippingType": "Local",
                "serviceType": "EB",
                "originGovernorateId": 1,
                "destinationGovernorateId": 12,
                "isCod": 1,
                "weightInGrams": str(weight),
                "destinationCountryId": 0
            }

            try:
                response = self.scraper.post(
                    self.url,
                    json=payload,
                    headers=self.headers
                )
                
                print(f"\nWeight: {weight}g")
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    self.safe_print_response(response.text)
                else:
                    print("Error:")
                    self.safe_print_response(response.text)
                    
            except Exception as e:
                print(f"Request failed for weight {weight}g: {str(e)}")

if __name__ == '__main__':
    unittest.main()
