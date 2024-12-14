import cloudscraper
import json
from enum import Enum
from flask import current_app
from functools import lru_cache
import logging
import requests
import urllib3
import ssl
from urllib3.util.ssl_ import create_urllib3_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure SSL context and disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
CIPHERS = 'DEFAULT:@SECLEVEL=1'

class ShippingProvider(Enum):
    EGYPOST = 'egypost'

class ShippingService:
    def __init__(self, provider: ShippingProvider):
        self.provider = provider
        self.base_url = "https://egyptpost.gov.eg"
        self.calculate_url = f"{self.base_url}/ar-EG/CalculatePostage/CalculatePostalFees"
        
        # Create a scraper instance with specific browser settings
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Headers for Arabic content - exactly matching test script
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/ar-EG/CalculatePostage"
        }
        
        # Initialize session
        try:
            # First get the main page to get any necessary cookies
            main_response = self.session.get(
                f"{self.base_url}/ar-EG/CalculatePostage",
                headers=self.headers,
                timeout=30
            )
            logger.info(f"Main page initialized with status code: {main_response.status_code}")
            
            if main_response.status_code == 200:
                logger.info("Session initialized successfully")
            else:
                logger.error(f"Failed to initialize main page. Status code: {main_response.status_code}")
                
        except Exception as e:
            logger.error(f"Error initializing EgyPost session: {str(e)}")

    def _hash_destination(self, destination):
        """Create a hashable key from destination dictionary"""
        return (
            str(destination.get('governorate_id', '')),
            str(destination.get('city', '')),
            str(destination.get('area', ''))
        )

    @lru_cache(maxsize=128)
    def get_available_services(self, destination_key, weight=0.5, is_cod=False):
        """Get available shipping services from EgyPost"""
        try:
            # Convert weight to grams (assuming input is in kg)
            weight_in_grams = int(weight * 1000)
            
            # Parse destination key back to components
            governorate_id, city, area = destination_key
            
            try:
                dest_governorate_id = int(governorate_id)
            except (ValueError, TypeError):
                dest_governorate_id = 1  # Default to Cairo if invalid
                logger.warning(f"Invalid governorate_id: {governorate_id}. Using default.")
            
            # Prepare the request payload exactly as EgyPost expects - matching test script
            payload = {
                "shippingType": "Local",
                "serviceType": "EB",
                "originGovernorateId": 1,  # Cairo
                "destinationGovernorateId": dest_governorate_id,
                "isCod": 1 if is_cod else 0,  # Convert boolean to 1/0
                "weightInGrams": str(weight_in_grams),  # Convert to string as expected
                "destinationCountryId": 0
            }

            # Log request details
            logger.info("EgyPost API Request:")
            logger.info(f"URL: {self.calculate_url}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")

            # Make the API request with explicit timeout
            response = self.session.post(
                self.calculate_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            # Log response details
            logger.info("EgyPost API Response:")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            
            try:
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Response Body: {json.dumps(data, indent=2)}")
                    
                    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                        services = []
                        for service in data['data']:
                            services.append({
                                'service_code': str(service.get('serviceCode', 'EB')),
                                'service_name': str(service.get('serviceName', 'Express Mail')),
                                'price': float(service.get('servicePrice', 0)),
                                'currency': 'EGP',
                                'estimated_days': int(service.get('periodInDays', 3)),
                                'features': [
                                    'Cash on Delivery' if is_cod else 'Prepaid',
                                    'Registered Mail',
                                    f'Weight: {weight}kg',
                                    f'Max Weight: {service.get("maxWeight", "N/A")} grams'
                                ]
                            })
                        return services
                    else:
                        logger.error(f"Unexpected response format: {data}")
                        return []
                else:
                    logger.error(f"API returned status code {response.status_code}")
                    logger.error(f"Response content: {response.text[:200]}...")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {str(e)}")
                logger.debug(f"Raw response: {response.text[:200]}...")
                return []
                
        except Exception as e:
            logger.error(f"Error calculating shipping: {str(e)}")
            return []

    def calculate_shipping(self, destination, weight=0.5, is_cod=False):
        """Wrapper method to handle the destination dictionary conversion"""
        destination_key = self._hash_destination(destination)
        return self.get_available_services(destination_key, weight, is_cod)
