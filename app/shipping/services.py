import json
import os
import logging
from logging.handlers import RotatingFileHandler
import requests
from flask import current_app
from datetime import datetime, timedelta
from functools import lru_cache
import threading

# Configure Bosta logger
bosta_logger = logging.getLogger('bosta')
bosta_logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create file handler for Bosta logs
bosta_handler = RotatingFileHandler(
    'logs/bosta.log',
    maxBytes=10485760,  # 10MB
    backupCount=10,
    encoding='utf-8'
)
bosta_handler.setLevel(logging.DEBUG)

# Create formatter
bosta_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    '%Y-%m-%d %H:%M:%S'
)
bosta_handler.setFormatter(bosta_formatter)

# Add handler to logger
bosta_logger.addHandler(bosta_handler)

# Initialize logger
logger = logging.getLogger(__name__)

class BostaCityMapping:
    """Mapping class for Bosta city codes and names"""
    
    CITIES = {
        'Cairo': {'ar': 'القاهرة', 'code': 'EG-01'},
        'Sohag': {'ar': 'سوهاج', 'code': 'EG-18'},
        'Alexandria': {'ar': 'الإسكندرية', 'code': 'EG-02'},
        'Menya': {'ar': 'المنيا', 'aliases': ['Minya'], 'code': 'EG-19'},
        'Dakahlia': {'ar': 'الدقهلية', 'code': 'EG-05'},
        'Luxor': {'ar': 'الأقصر', 'code': 'EG-22'},
        'Behira': {'ar': 'البحيرة', 'aliases': ['Beheira'], 'code': 'EG-04'},
        'Ismailia': {'ar': 'الإسماعيلية', 'aliases': ['Isamilia'], 'code': 'EG-11'},
        'Assuit': {'ar': 'أسيوط', 'aliases': ['Asyut'], 'code': 'EG-17'},
        'Aswan': {'ar': 'أسوان', 'code': 'EG-21'},
        'Suez': {'ar': 'السويس', 'code': 'EG-12'},
        'Monufia': {'ar': 'المنوفية', 'aliases': ['Menofia'], 'code': 'EG-09'},
        'Sharqia': {'ar': 'الشرقية', 'code': 'EG-10'},
        'Gharbia': {'ar': 'الغربية', 'code': 'EG-07'},
        'Kafr Alsheikh': {'ar': 'كفر الشيخ', 'aliases': ['Kafr Al-Sheikh'], 'code': 'EG-08'},
        'El Kalioubia': {'ar': 'القليوبية', 'aliases': ['Qalyubia'], 'code': 'EG-06'},
        'North Coast': {'ar': 'الساحل الشمالي', 'code': 'EG-03'},
        'Qena': {'ar': 'قنا', 'code': 'EG-20'},
        'Bani Suif': {'ar': 'بني سويف', 'aliases': ['Beni Suef'], 'code': 'EG-16'},
        'Damietta': {'ar': 'دمياط', 'code': 'EG-14'},
        'Red Sea': {'ar': 'البحر الأحمر', 'code': 'EG-23'},
        'Fayoum': {'ar': 'الفيوم', 'aliases': ['Faiyum'], 'code': 'EG-15'},
        'Port Said': {'ar': 'بور سعيد', 'code': 'EG-13'},
        'New Valley': {'ar': 'الوادى الجديد', 'code': 'EG-24'},
        'Giza': {'ar': 'الجيزة', 'code': 'EG-25'},
        'Matrouh': {'ar': 'مرسى مطروح', 'code': 'EG-28'},
        'North Sinai': {'ar': 'شمال سيناء', 'code': 'EG-27'},
        'South Sinai': {'ar': 'جنوب سيناء', 'code': 'EG-26'}
    }

    @classmethod
    def get_city_choices(cls):
        """Get list of city choices for forms"""
        return [(city, f"{city} ({data['ar']})") for city, data in sorted(cls.CITIES.items())]

    @classmethod
    def get_code(cls, city_name):
        """Get city code for a given city name"""
        if not city_name:
            return None
            
        # Direct match
        if city_name in cls.CITIES:
            return cls.CITIES[city_name]['code']
            
        # Arabic name match
        for city, data in cls.CITIES.items():
            if data['ar'] == city_name:
                return data['code']
                
        # Alias match
        for city, data in cls.CITIES.items():
            if 'aliases' in data and city_name in data['aliases']:
                return data['code']
                
        # Case-insensitive match
        city_upper = city_name.upper()
        for city, data in cls.CITIES.items():
            if city.upper() == city_upper:
                return data['code']
                
        return None

    @classmethod
    def normalize_name(cls, city_name):
        """Normalize city name to standard English form"""
        if not city_name:
            return None
            
        # Direct match
        if city_name in cls.CITIES:
            return city_name
            
        # Arabic name match
        for city, data in cls.CITIES.items():
            if data['ar'] == city_name:
                return city
                
        # Alias match
        for city, data in cls.CITIES.items():
            if 'aliases' in data and city_name in data['aliases']:
                return city
                
        # Case-insensitive match
        city_upper = city_name.upper()
        for city in cls.CITIES:
            if city.upper() == city_upper:
                return city
                
        return None

class BostaShippingService:
    """Service class for Bosta shipping integration"""
    
    # Class-level cache for token and location
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement singleton pattern to ensure one instance per application"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, email=None, password=None, api_key=None):
        """Initialize Bosta shipping service"""
        if not hasattr(self, '_initialized'):
            self.email = email or current_app.config.get('BOSTA_EMAIL')
            self.password = password or current_app.config.get('BOSTA_PASSWORD')
            self.api_key = api_key or current_app.config.get('BOSTA_API_KEY')
            self.base_url = "https://app.bosta.co/api/v2"
            self._token = None
            self._token_expiry = None
            self._default_location = None
            self._location_expiry = None
            
            # Log configuration for debugging
            bosta_logger.debug(f"Initialized Bosta service with email: {self.email}")
            bosta_logger.debug(f"API Key present: {'Yes' if self.api_key else 'No'}")
            
            if not all([self.email, self.password, self.api_key]):
                error_msg = "Missing Bosta credentials. Please check your configuration."
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            self._initialized = True
    
    @property
    def token(self):
        """Get the authentication token, refreshing if needed"""
        now = datetime.now()
        if not self._token or not self._token_expiry or now >= self._token_expiry:
            self._login()
        return self._token
    
    @token.setter
    def token(self, value):
        """Set the authentication token with expiry"""
        self._token = value
        self._token_expiry = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour

    @property
    def headers(self):
        """Get headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "ApiKey": self.api_key
        }
        
    def _login(self):
        """Authenticate with Bosta API"""
        try:
            bosta_logger.info(f"Authenticating with Bosta using email: {self.email}")
            
            # Log headers for debugging
            auth_header = f"Bearer {self.api_key}" if self.api_key else None
            bosta_logger.debug(f"Using Authorization header: {auth_header}")
            
            response = requests.post(
                f"{self.base_url}/users/login",
                json={
                    "email": self.email,
                    "password": self.password
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": auth_header
                },
                timeout=30
            )
            
            # Log raw response for debugging
            bosta_logger.debug(f"Login Response Status: {response.status_code}")
            bosta_logger.debug(f"Login Response Headers: {dict(response.headers)}")
            response_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
            bosta_logger.debug(f"Login Response Body: {response_text}")
            
            if response.status_code != 200:
                error_msg = f"Failed to authenticate with Bosta. Status: {response.status_code}, Response: {response.text}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            data = response.json()
            if not data.get('success'):
                error_msg = f"Authentication failed: {data.get('message', 'Unknown error')}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Token comes with "Bearer " prefix already
            token = data.get('data', {}).get('token')
            if not token:
                error_msg = "No token received from Bosta API"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Remove "Bearer " prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
                
            # Store token and update headers
            self.token = token
            bosta_logger.debug(f"Received token: {token[:10]}...")
            bosta_logger.info("Successfully authenticated with Bosta")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to Bosta API: {str(e)}"
            bosta_logger.error(error_msg)
            raise ValueError(error_msg)
            
    def _ensure_token(self):
        """Ensure we have a valid token for API calls"""
        if not self.token:
            self._login()
            
    def get_cities(self):
        """Get list of cities from Bosta API"""
        try:
            if not self.token:
                self._login()
                
            response = requests.get(
                f"{self.base_url}/cities",
                headers=self.headers,
                timeout=30
            )
            
            # Log raw response for debugging
            bosta_logger.info(f"Bosta Cities API Response Status: {response.status_code}")
            bosta_logger.debug(f"Bosta Cities API Response Headers: {dict(response.headers)}")
            
            # Log first 1000 characters of response for debugging
            response_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
            bosta_logger.debug(f"Bosta Cities API Response Body (truncated): {response_text}")
            
            if response.status_code != 200:
                error_msg = f"Failed to get cities from Bosta. Status: {response.status_code}, Response: {response.text}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Parse response data
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response from Bosta API: {str(e)}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            if not response_data.get('success'):
                error_msg = f"API error: {response_data.get('message', 'Unknown error')}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Cities are in the data list
            cities_data = response_data.get('data', {}).get('list', [])
            if not cities_data:
                error_msg = "No cities data returned from Bosta API"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Log available cities for debugging
            city_names = [(c.get('name', ''), c.get('nameAr', ''), c.get('code', '')) for c in cities_data]
            bosta_logger.debug(f"Available cities from Bosta API (name, nameAr, code): {city_names}")
            
            return cities_data
            
        except Exception as e:
            bosta_logger.error(f"Error getting cities: {str(e)}")
            raise ValueError(f"Failed to get cities: {str(e)}")
    
    @property
    def token_valid(self):
        """Check if current token is valid"""
        if not self._token:
            return False
            
        # Check if token is valid by making a test API call
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=headers
            )
            if response.status_code == 401:
                self._login()
                return bool(self.token)
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False

    def calculate_shipping_cost(self, order_id, weight, dimensions, city):
        """Calculate shipping cost with caching"""
        if not self.token or not self.default_location:
            return None
            
        cache_key = f"{order_id}_{weight}_{dimensions}_{city}"
        bosta_logger.debug(f"Calculating shipping cost for: {cache_key}")
        
        try:
            # Your existing shipping cost calculation code here
            # The @lru_cache decorator will handle caching the results
            
            response = requests.post(
                f"{self.base_url}/deliveries/rate",
                headers=self.headers,
                json={
                    "type": 10,
                    "pickupLocationId": self.default_location['_id'],
                    "dropOffAddress": {
                        "city": city
                    },
                    "packageDetails": {
                        "weight": weight,
                        "dimensions": dimensions
                    }
                }
            )
            
            if response.status_code != 200:
                bosta_logger.error(f"Failed to calculate shipping cost: {response.text}")
                return None
                
            cost = response.json().get('data', {}).get('price', 0)
            bosta_logger.info(f"Calculated total shipping cost: {cost}")
            return cost
            
        except Exception as e:
            bosta_logger.error(f"Error calculating shipping cost: {str(e)}")
            return None

    def create_shipping_order(self, order):
        """Create shipping order with Bosta"""
        try:
            # Ensure we have a valid token
            self._ensure_token()
            
            # Prepare payload
            payload = self._prepare_delivery_payload(order)
            if not payload:
                raise ValueError("Failed to prepare delivery payload")
            
            # Make API request
            try:
                response = requests.post(
                    f"{self.base_url}/deliveries",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                # Log response for debugging
                bosta_logger.info(f"Bosta Create Delivery Response Status: {response.status_code}")
                bosta_logger.debug(f"Bosta Create Delivery Response Headers: {dict(response.headers)}")
                response_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                bosta_logger.debug(f"Bosta Create Delivery Response Body: {response_text}")
                
                # According to bosta.yaml, both 200 and 201 are success codes
                if response.status_code not in [200, 201]:
                    error_msg = f"Failed to create Bosta delivery. Status: {response.status_code}, Response: {response.text}"
                    bosta_logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # Parse response
                response_data = response.json()
                if not response_data.get('success'):
                    error_msg = f"Failed to create Bosta delivery: {response_data.get('message', 'Unknown error')}"
                    bosta_logger.error(error_msg)
                    raise ValueError(error_msg)
                
                delivery_data = response_data.get('data', {})
                
                # Log success
                bosta_logger.info(f"Successfully created Bosta delivery with tracking number: {delivery_data.get('trackingNumber')}")
                
                # Return delivery details
                return {
                    'delivery_id': delivery_data.get('_id'),
                    'tracking_number': delivery_data.get('trackingNumber'),
                    'status': delivery_data.get('state', {}).get('value', 'PENDING'),
                    'status_code': delivery_data.get('state', {}).get('code', 0),
                    'created_at': delivery_data.get('createdAt')
                }
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to connect to Bosta API: {str(e)}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
            
        except Exception as e:
            bosta_logger.error(f"Error creating Bosta delivery: {str(e)}")
            raise

    def _prepare_delivery_payload(self, order):
        """Prepare delivery payload for Bosta API"""
        try:
            if not order:
                raise ValueError("Order is required")
                
            if not order.shipping_address:
                raise ValueError("Shipping address is required")
                
            if not self._default_location:
                self._default_location = self._get_default_location()
                if not self._default_location:
                    raise ValueError("No pickup location configured")

            # Get zone and district IDs for dropoff city
            zone_id, district_id = self._get_zone_and_district(order.shipping_address.city)
            
            # Get receiver information from shipping address
            receiver_name = order.shipping_address.name.strip()
            name_parts = receiver_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else first_name
            
            # Extract pickup address from default location
            pickup_address = self._default_location.get('address', {})
            pickup_city = pickup_address.get('city', {})
            pickup_zone = pickup_address.get('zone', {})
            pickup_district = pickup_address.get('district', {})
            
            # Calculate COD amount if needed
            is_cod = order.payment_method == 'cod'
            cod_amount = float(order.total) if is_cod else 0
            
            # Prepare the delivery payload
            payload = {
                "type": 10,  # Regular delivery
                "specs": {
                    "size": "SMALL",
                    "packageDetails": {
                        "itemsCount": len(order.items),
                        "description": f"Order #{order.id}"
                    }
                },
                "pickupAddress": {
                    "cityCode": pickup_city.get('_id'),
                    "zone": {
                        "_id": pickup_zone.get('_id'),
                        "name": pickup_zone.get('name', '')
                    },
                    "district": {
                        "_id": pickup_district.get('_id'),
                        "name": pickup_district.get('name', '')
                    },
                    "firstLine": pickup_address.get('firstLine', ''),
                    "buildingNumber": pickup_address.get('buildingNumber', '')
                },
                "dropOffAddress": {
                    "cityCode": zone_id,
                    "zone": {
                        "_id": zone_id,
                        "name": order.shipping_address.city
                    },
                    "district": {
                        "_id": district_id,
                        "name": order.shipping_address.district or order.shipping_address.city
                    },
                    "firstLine": order.shipping_address.street,
                    "buildingNumber": order.shipping_address.building_number or "1"
                },
                "receiver": {
                    "firstName": str(first_name),
                    "lastName": str(last_name),
                    "phone": str(order.shipping_address.phone),
                    "email": str(order.user.email) if order.user else None
                },
                "cod": cod_amount,  # Set COD amount directly
                "allowToOpenPackage": True,
                "businessReference": str(order.id)
            }
            
            # Add COD amount to specs if COD payment
            if is_cod:
                payload["specs"]["cod"] = cod_amount
            
            bosta_logger.debug(f"Prepared delivery payload: {payload}")
            return payload
            
        except Exception as e:
            bosta_logger.error(f"Error preparing delivery payload: {str(e)}")
            raise

    def _get_default_location(self):
        """Get default pickup location"""
        try:
            # Ensure we have a valid token
            if not self.token:
                bosta_logger.info("No token available, attempting to login")
                self._login()
                
            # Get default location data
            bosta_logger.info("Fetching default pickup location")
            try:
                # Make API request
                response = requests.get(
                    f"{self.base_url}/pickup-locations",
                    headers=self.headers,
                    timeout=30
                )
                
                # Log raw response for debugging
                bosta_logger.info(f"Bosta Pickup Locations API Response Status: {response.status_code}")
                bosta_logger.debug(f"Bosta Pickup Locations API Response Headers: {dict(response.headers)}")
                
                # Log first 1000 characters of response for debugging
                response_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                bosta_logger.debug(f"Bosta Pickup Locations API Response Body (truncated): {response_text}")
                
                if response.status_code == 401:
                    # Token might be expired, try to refresh
                    bosta_logger.info("Token might be expired, attempting to refresh")
                    self._token = None  # Force new token
                    self._login()
                    
                    # Retry the request
                    response = requests.get(
                        f"{self.base_url}/pickup-locations",
                        headers=self.headers,
                        timeout=30
                    )
                
                if response.status_code != 200:
                    error_msg = f"Failed to get pickup locations: {response.text}"
                    bosta_logger.error(error_msg)
                    return None
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to connect to Bosta Pickup Locations API: {str(e)}"
                bosta_logger.error(error_msg)
                return None
                
            # Parse response data
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response from Bosta API: {str(e)}"
                bosta_logger.error(error_msg)
                return None
                
            # Check response
            if not response_data.get('success'):
                error_msg = f"Failed to get pickup locations: {response_data.get('message', 'Unknown error')}"
                bosta_logger.error(error_msg)
                return None
                
            # Locations are in the 'list' array inside 'data'
            locations = response_data.get('data', {}).get('list', [])
            
            if not locations:
                error_msg = "No pickup locations found"
                bosta_logger.error(error_msg)
                return None
                
            # Find the default location or use the first one
            default_location = next(
                (loc for loc in locations if loc.get('isDefault')),
                locations[0] if locations else None
            )
            
            if not default_location:
                error_msg = "No valid pickup location found"
                bosta_logger.error(error_msg)
                return None
                
            bosta_logger.info(f"Found default pickup location: {default_location.get('locationName', 'Unknown')}")
            
            # Return the entire location object as it contains all necessary data
            return default_location
            
        except Exception as e:
            bosta_logger.error(f"Error fetching pickup locations: {str(e)}")
            return None

    def _get_zone_and_district(self, city_name):
        """Get zone and district IDs for a city from Bosta API"""
        try:
            # Ensure we have a valid token
            if not self.token:
                bosta_logger.info("No token available, attempting to login")
                self._login()
                
            # Normalize city name for better matching
            city_name = city_name.strip().lower()
            bosta_logger.info(f"Getting zone and district IDs for city: {city_name}")
            
            # Get city data from Bosta API
            try:
                response = requests.get(
                    f"{self.base_url}/cities",
                    headers=self.headers,
                    timeout=30
                )
                
                # Log raw response for debugging
                bosta_logger.info(f"Bosta Cities API Response Status: {response.status_code}")
                bosta_logger.debug(f"Bosta Cities API Response Headers: {dict(response.headers)}")
                
                # Log first 1000 characters of response for debugging
                response_text = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                bosta_logger.debug(f"Bosta Cities API Response Body (truncated): {response_text}")
                
                if response.status_code != 200:
                    error_msg = f"Failed to get cities from Bosta. Status: {response.status_code}, Response: {response.text}"
                    bosta_logger.error(error_msg)
                    raise ValueError(error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to connect to Bosta Cities API: {str(e)}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Parse response data
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON response from Bosta API: {str(e)}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            if not response_data.get('success'):
                error_msg = f"API error: {response_data.get('message', 'Unknown error')}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Cities are in the data list
            cities_data = response_data.get('data', {}).get('list', [])
            if not cities_data:
                error_msg = "No cities data returned from Bosta API"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Log available cities for debugging
            city_names = [(c.get('name', ''), c.get('nameAr', ''), c.get('code', '')) for c in cities_data]
            bosta_logger.debug(f"Available cities from Bosta API (name, nameAr, code): {city_names}")
            
            # Find matching city by name or code
            city = None
            for c in cities_data:
                current_city_name = c.get('name', '').strip().lower()
                current_city_name_ar = c.get('nameAr', '').strip()
                current_city_code = c.get('code', '').strip().lower()
                
                bosta_logger.debug(f"Comparing '{city_name}' with name:'{current_city_name}', nameAr:'{current_city_name_ar}', code:'{current_city_code}'")
                
                # Check all possible matches
                if city_name in (current_city_name, current_city_name_ar, current_city_code):
                    city = c
                    bosta_logger.info(f"Found city match: {c}")
                    break
                    
            if not city:
                error_msg = f"City not found in Bosta API: {city_name}. Available cities: {city_names}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Get city ID as zone ID
            zone_id = city.get('_id')
            if not zone_id:
                error_msg = f"No ID found for city: {city_name}"
                bosta_logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Get first district ID from the city's zones
            district_id = None
            if 'zones' in city:
                zones = city.get('zones', [])
                if zones and 'districts' in zones[0]:
                    districts = zones[0].get('districts', [])
                    if districts:
                        district_id = districts[0].get('_id')
            
            # If no district found, use city ID as district ID
            if not district_id:
                district_id = zone_id
                
            bosta_logger.info(f"Found zone ID: {zone_id} and district ID: {district_id} for city: {city_name}")
            return zone_id, district_id
            
        except Exception as e:
            bosta_logger.error(f"Error getting zone and district IDs: {str(e)}")
            raise ValueError(f"Failed to get zone and district IDs: {str(e)}")

    def estimate_shipping_cost(self, pickup_city, dropoff_city, cod_amount=0):
        """Estimate shipping cost between two cities"""
        try:
            if not self.token and not self._login():
                bosta_logger.error("Failed to authenticate with Bosta")
                return None

            # Normalize city names to standard English form
            pickup_city = BostaCityMapping.normalize_name(pickup_city)
            dropoff_city = BostaCityMapping.normalize_name(dropoff_city)

            if not pickup_city or not dropoff_city:
                bosta_logger.error(f"Invalid city names: pickup={pickup_city}, dropoff={dropoff_city}")
                return None

            params = {
                'cod': cod_amount,
                'pickupCity': pickup_city,
                'dropOffCity': dropoff_city,
                'size': 'MEDIUM',
                'type': 'SEND'  # Using SEND from allowed types: [SEND, CASH_COLLECTION, CUSTOMER_RETURN_PICKUP, EXCHANGE, SIGN_AND_RETURN]
            }

            response = requests.get(
                f"{self.base_url}/pricing/shipment/calculator",
                headers=self.headers,
                params=params
            )

            if response.status_code != 200:
                bosta_logger.error(f"Error estimating shipping cost: {response.status_code} {response.reason} for url: {response.url}")
                bosta_logger.error(f"Response content: {response.text}")
                return None

            data = response.json()
            # Extract the base shipping cost from the tier
            if 'data' in data and 'tier' in data['data'] and 'cost' in data['data']['tier']:
                base_cost = float(data['data']['tier']['cost'])
                
                # Add opening package fee if applicable
                if ('openingPackageFee' in data['data']['tier'] and 
                    'amount' in data['data']['tier']['openingPackageFee']):
                    base_cost += float(data['data']['tier']['openingPackageFee']['amount'])
                
                # Add bosta material fee if applicable
                if ('bostaMaterialFee' in data['data']['tier'] and 
                    'amount' in data['data']['tier']['bostaMaterialFee']):
                    base_cost += float(data['data']['tier']['bostaMaterialFee']['amount'])
                
                # Calculate COD fee if applicable
                if cod_amount > 0 and 'extraCodFee' in data['data']['tier']:
                    cod_fee = data['data']['tier']['extraCodFee']
                    if 'percentage' in cod_fee:
                        cod_fee_amount = float(cod_fee['percentage']) * cod_amount
                        if 'minimumFeeAmount' in cod_fee:
                            cod_fee_amount = max(cod_fee_amount, float(cod_fee['minimumFeeAmount']))
                        base_cost += cod_fee_amount
                
                bosta_logger.info(f"Calculated total shipping cost: {base_cost}")
                return base_cost
            else:
                bosta_logger.error(f"Unexpected response format: {data}")
                return None

        except Exception as e:
            bosta_logger.error(f"Error in estimate_shipping_cost: {str(e)}")
            return None

    def get_cod_fee(self, base_cost):
        """Calculate cash on delivery fee based on the base shipping cost"""
        # Bosta typically charges 1% of the shipping cost for COD, minimum 10 EGP
        cod_fee = max(base_cost * 0.01, 10)
        return cod_fee

    def track_shipment(self, tracking_number):
        """Track shipment status with Bosta"""
        try:
            if not self.token and not self._login():
                raise Exception("Failed to authenticate with Bosta")
            
            response = requests.get(
                f"{self.base_url}/deliveries/tracking/{tracking_number}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                raise Exception(f"Failed to track shipment: {response.text}")
                
        except Exception as e:
            bosta_logger.error(f"Error tracking shipment: {str(e)}")
            raise

    def cancel_shipping_order(self, delivery_id):
        """Cancel a delivery order with Bosta"""
        try:
            if not self.token and not self._login():
                raise Exception("Failed to authenticate with Bosta")

            # Call Bosta's terminate delivery API
            response = requests.delete(
                f"{self.base_url}/deliveries/business/{delivery_id}/terminate",
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    bosta_logger.info(f"Successfully cancelled Bosta delivery: {delivery_id}")
                    return True
                else:
                    error_msg = data.get('message', 'Unknown error from Bosta API')
                    bosta_logger.error(f"Bosta API error while cancelling delivery: {error_msg}")
                    raise Exception(error_msg)
            else:
                error_msg = f"Failed to cancel Bosta delivery. Status: {response.status_code}, Response: {response.text}"
                bosta_logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            bosta_logger.error(f"Error cancelling Bosta delivery: {str(e)}")
            raise

def calculate_shipping_cost(order, carrier_code=None):
    """Calculate shipping cost for an order"""
    if carrier_code != 'bosta':
        raise ValueError("Only Bosta shipping is supported")
        
    service = BostaShippingService()
    return service.calculate_shipping_cost(order.id, order.weight, order.dimensions, order.city)

def create_shipping_order(order):
    """Create shipping order with Bosta"""
    if not order.shipping_carrier or order.shipping_carrier.code != 'bosta':
        raise ValueError("Only Bosta shipping is supported")
        
    service = BostaShippingService()
    return service.create_shipping_order(order)

def track_shipment(order):
    """Track shipment status"""
    if not order.shipping_carrier or order.shipping_carrier.code != 'bosta':
        raise ValueError("Only Bosta shipping is supported")
        
    if not order.delivery_tracking_number:
        raise ValueError("No tracking number available")
        
    service = BostaShippingService()
    return service.track_shipment(order.delivery_tracking_number)

def cancel_shipping_order(order):
    """Cancel a shipping order with the shipping provider"""
    if not order.delivery_order_id:
        return False
        
    try:
        shipping_service = BostaShippingService()
        return shipping_service.cancel_shipping_order(order.delivery_order_id)
    except Exception as e:
        bosta_logger.error(f"Failed to cancel shipping order: {str(e)}")
        return False
