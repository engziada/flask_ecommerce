from datetime import datetime, timedelta
import requests
import json
import os
from flask import current_app
from app import db
from app.models.shipping import ShippingCarrier, ShippingMethod, ShippingQuote
from .cities import normalize_city_name, get_city_code

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
    """Bosta shipping service implementation"""
    
    def __init__(self):
        self.base_url = "https://app.bosta.co/api/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.token = None
        self.default_location = None
    
    def _login(self):
        """Helper method to authenticate with Bosta"""
        login_payload = {
            "email": current_app.config['BOSTA_EMAIL'],
            "password": current_app.config['BOSTA_PASSWORD']
        }
        
        try:
            current_app.logger.info(f"Attempting to login to Bosta with email: {login_payload['email']}")
            response = requests.post(
                f"{self.base_url}/users/login",
                headers=self.headers,
                json=login_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('data', {}).get('token'):
                    current_app.logger.error(f"No token in response: {data}")
                    return False
                    
                # Get the raw token and clean it up
                raw_token = data['data']['token']
                # Remove 'Bearer' and any extra spaces
                token = raw_token.replace('Bearer', '').strip()
                
                # Log success for debugging
                current_app.logger.info(f"Successfully got token for email: {login_payload['email']}")
                current_app.logger.debug(f"Token: {token[:10]}...")
                
                self.token = token
                # When using the token in headers, add back the 'Bearer' prefix
                self.headers["Authorization"] = f"Bearer {token}"
                return True
            else:
                current_app.logger.error(f"Login failed with status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return False
    
    def _get_default_location(self):
        """Helper method to get default pickup location"""
        if not self.token:
            current_app.logger.info("No token available, attempting to login")
            if not self._login():
                return False
                
        try:
            current_app.logger.info("Fetching default pickup location")
            response = requests.get(
                f"{self.base_url}/pickup-locations",
                headers=self.headers
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Failed to get locations. Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            if 'data' not in data:
                current_app.logger.error("Response missing 'data' field")
                return False
                
            if 'list' not in data['data']:
                current_app.logger.error("Response data missing 'list' field")
                return False
                
            locations = data['data']['list']
            if not isinstance(locations, list) or not locations:
                current_app.logger.error("No locations found or invalid format")
                return False
            
            # Get the first location
            location = locations[0]
            if 'address' not in location:
                current_app.logger.error("Location missing 'address' field")
                return False
                
            current_app.logger.info(f"Found default pickup location: {location.get('locationName', 'Unknown')}")
            self.default_location = location
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error getting default location: {str(e)}")
            return False
    
    def calculate_shipping_cost(self, order):
        """Calculate shipping cost using Bosta's rates"""
        try:
            current_app.logger.info("Starting shipping cost calculation")
            
            if not self.token and not self._login():
                raise Exception("Failed to authenticate with Bosta")
                
            if not self.default_location and not self._get_default_location():
                raise Exception("No pickup location available")
            
            # Get carrier
            carrier = ShippingCarrier.query.filter_by(code='bosta').first()
            if not carrier:
                raise Exception("Bosta carrier not configured")
            
            current_app.logger.info(f"Found carrier: {carrier}")
            
            # Get shipping address
            address = order.shipping_address
            if not address:
                raise Exception("No shipping address provided")
            
            # Extract and validate city
            delivery_city = address.city
            normalized_city, city_code = normalize_city_name(delivery_city)
            if not city_code:
                current_app.logger.error(f"Invalid city name provided: {delivery_city}")
                return []
            
            # Prepare pickup address
            try:
                pickup_address = {
                    'city': self.default_location['address'].get('city', {}).get('name', 'Cairo'),
                    'district': self.default_location['address'].get('district', ''),
                    'firstLine': self.default_location['address'].get('firstLine', ''),
                    'buildingNumber': self.default_location['address'].get('buildingNumber', ''),
                    'apartment': self.default_location['address'].get('apartment', ''),
                    'floor': self.default_location['address'].get('floor', ''),
                    'cityCode': get_city_code(self.default_location['address'].get('city', {}).get('name', 'Cairo')) or ''
                }
            except (KeyError, TypeError) as e:
                current_app.logger.error(f"Error extracting pickup address: {str(e)}")
                return []
            
            # Prepare delivery address
            delivery = {
                'city': normalized_city,
                'district': address.district or '',
                'firstLine': address.street or '',
                'buildingNumber': address.building_number or '',
                'apartment': address.apartment or '',
                'floor': address.floor or '',
                'cityCode': city_code
            }
            
            # Calculate cost for each method
            quotes = []
            for method in carrier.methods:
                if not method.is_active:
                    current_app.logger.info(f"Skipping inactive method: {method}")
                    continue
                
                current_app.logger.info(f"Calculating cost for method: {method}")
                
                # Prepare estimation payload
                payload = {
                    "type": 10 if method.code == 'express' else 20,
                    "specs": {
                        "packageType": "Parcel",
                        "size": "MEDIUM",
                        "packageDetails": {
                            "itemsCount": len(order.items),
                            "description": f"Order {order.id}"
                        }
                    },
                    "cod": float(order.total) if order.payment_method == 'cod' else 0,
                    "dropOffAddress": delivery,
                    "pickupAddress": pickup_address
                }
                
                current_app.logger.info(f"Sending estimation request with payload: {payload}")
                
                try:
                    response = requests.post(
                        f"{self.base_url}/delivery/estimate",
                        headers=self.headers,
                        json=payload
                    )
                    
                    current_app.logger.info(f"Got response: Status={response.status_code}, Body={response.text}")
                    
                    if response.status_code == 200:
                        data = response.json()['data']
                        quotes.append({
                            'method_id': method.id,
                            'method_name': method.name,
                            'method_code': method.code,
                            'cost': data['totalCost'],
                            'currency': 'EGP',
                            'estimated_days': method.estimated_days
                        })
                    else:
                        current_app.logger.error(f"Failed to get estimate. Status: {response.status_code}, Response: {response.text}")
                        
                except Exception as e:
                    current_app.logger.error(f"Error getting estimate for method {method.name}: {str(e)}")
            
            if not quotes:
                current_app.logger.error("No shipping quotes available")
                return []
                
            current_app.logger.info(f"Successfully calculated shipping quotes: {quotes}")
            return quotes
            
        except Exception as e:
            current_app.logger.error(f"Error calculating shipping cost: {str(e)}")
            raise
    
    def create_shipping_order(self, order):
        """Create shipping order with Bosta"""
        try:
            if not self.token and not self._login():
                raise Exception("Failed to authenticate with Bosta")
                
            if not self.default_location and not self._get_default_location():
                raise Exception("No pickup location available")
            
            # Get shipping address
            address = order.shipping_address
            if not address:
                raise Exception("No shipping address provided")
            
            # Extract and validate city
            delivery_city = address.city
            normalized_city, city_code = normalize_city_name(delivery_city)
            if not city_code:
                current_app.logger.error(f"Invalid city name provided: {delivery_city}")
                return None
            
            # Prepare pickup address
            try:
                pickup_address = {
                    'city': self.default_location['address'].get('city', {}).get('name', 'Cairo'),
                    'district': self.default_location['address'].get('district', ''),
                    'firstLine': self.default_location['address'].get('firstLine', ''),
                    'buildingNumber': self.default_location['address'].get('buildingNumber', ''),
                    'apartment': self.default_location['address'].get('apartment', ''),
                    'floor': self.default_location['address'].get('floor', ''),
                    'cityCode': get_city_code(self.default_location['address'].get('city', {}).get('name', 'Cairo')) or ''
                }
            except (KeyError, TypeError) as e:
                current_app.logger.error(f"Error extracting pickup address: {str(e)}")
                return None
            
            # Prepare delivery address
            delivery = {
                'city': normalized_city,
                'district': address.district or '',
                'firstLine': address.street or '',
                'buildingNumber': address.building_number or '',
                'apartment': address.apartment or '',
                'floor': address.floor or '',
                'cityCode': city_code
            }
            
            # Create delivery payload
            payload = {
                "type": 10 if order.shipping_method.code == 'express' else 20,
                "specs": {
                    "packageType": "Parcel",
                    "size": "MEDIUM",
                    "packageDetails": {
                        "itemsCount": len(order.items),
                        "description": f"Order {order.id}"
                    }
                },
                "notes": f"Order {order.id}",
                "cod": float(order.total) if order.payment_method == 'cod' else 0,
                "dropOffAddress": delivery,
                "pickupAddress": pickup_address,
                "businessReference": f"order_{order.id}",
                "receiver": {
                    "firstName": address.name.split()[0],
                    "lastName": address.name.split()[-1] if len(address.name.split()) > 1 else "",
                    "phone": address.phone,
                    "email": order.user.email
                }
            }
            
            # Create delivery
            response = requests.post(
                f"{self.base_url}/deliveries",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                delivery_data = response.json()['data']
                
                # Update order with delivery information
                order.delivery_order_id = delivery_data['_id']
                order.delivery_tracking_number = delivery_data['trackingNumber']
                order.delivery_status = delivery_data['state']['value']
                order.delivery_status_code = str(delivery_data['state']['code'])
                order.delivery_created_at = datetime.utcnow()
                order.delivery_updated_at = datetime.utcnow()
                
                db.session.commit()
                return delivery_data
            else:
                raise Exception(f"Failed to create delivery: {response.text}")
                
        except Exception as e:
            current_app.logger.error(f"Error creating shipping order: {str(e)}")
            raise
    
    def _ensure_token(self):
        """Ensure we have a valid token for API calls"""
        if not self.token:
            self._login()
            
        if not self.token:
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

    def estimate_shipping_cost(self, pickup_city, dropoff_city, cod_amount=0):
        """Estimate shipping cost between two cities"""
        try:
            if not self.token and not self._login():
                current_app.logger.error("Failed to authenticate with Bosta")
                return None

            # Normalize city names to standard English form
            pickup_city = BostaCityMapping.normalize_name(pickup_city)
            dropoff_city = BostaCityMapping.normalize_name(dropoff_city)

            if not pickup_city or not dropoff_city:
                current_app.logger.error(f"Invalid city names: pickup={pickup_city}, dropoff={dropoff_city}")
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
                current_app.logger.error(f"Error estimating shipping cost: {response.status_code} {response.reason} for url: {response.url}")
                current_app.logger.error(f"Response content: {response.text}")
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
                
                current_app.logger.info(f"Calculated total shipping cost: {base_cost}")
                return base_cost
            else:
                current_app.logger.error(f"Unexpected response format: {data}")
                return None

        except Exception as e:
            current_app.logger.error(f"Error in estimate_shipping_cost: {str(e)}")
            return None

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
            current_app.logger.error(f"Error tracking shipment: {str(e)}")
            raise

def calculate_shipping_cost(order, carrier_code=None):
    """Calculate shipping cost for an order"""
    if carrier_code != 'bosta':
        raise ValueError("Only Bosta shipping is supported")
        
    service = BostaShippingService()
    return service.calculate_shipping_cost(order)

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