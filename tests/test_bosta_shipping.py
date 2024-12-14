import os
import unittest
import requests
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import current_app
from app import create_app, db
from app.models.address import Address
from app.shipping.services import BostaShippingService, BostaCityMapping
from config import TestingConfig

# Load environment variables from .env file
load_dotenv()

class TestBostaShipping(unittest.TestCase):
    """Test suite for Bosta shipping integration"""

    @classmethod
    def setUpClass(cls):
        """Set up test class with base configuration"""
        cls.base_url = "https://app.bosta.co/api/v2"
        cls.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Login and store token
        cls.token = cls._login()
        if cls.token:
            cls.headers["Authorization"] = f"Bearer {cls.token}"
        
        # Get and store default pickup location
        cls.default_location = cls._get_default_location()
    
    @classmethod
    def _login(cls):
        """Helper method to authenticate with Bosta"""
        login_payload = {
            "email": os.getenv('BOSTA_EMAIL'),
            "password": os.getenv('BOSTA_PASSWORD')
        }
        
        try:
            response = requests.post(
                f"{cls.base_url}/users/login",
                headers=cls.headers,
                json=login_payload
            )
            
            if response.status_code == 200:
                return response.json()['data']['token']
            else:
                print(f"Login failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            return None
    
    @classmethod
    def _get_default_location(cls):
        """Helper method to get default pickup location"""
        try:
            response = requests.get(
                f"{cls.base_url}/pickup-locations",
                headers=cls.headers
            )
            
            if response.status_code == 200:
                locations = response.json()['data']['list']
                for location in locations:
                    if location.get('isDefault'):
                        return location
            
            print("No default pickup location found")
            return None
            
        except Exception as e:
            print(f"Error getting pickup locations: {str(e)}")
            return None
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Initialize service
        self.service = BostaShippingService()
        self.base_url = "https://app.bosta.co/api/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Get fresh token
        token = self.get_token()
        if token:
            self.service.token = token
            self.service.headers["Authorization"] = f"Bearer {token}"
            self.headers["Authorization"] = f"Bearer {token}"
        else:
            self.fail("Failed to get token during setup")

    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
    
    def get_token(self):
        """Helper method to get authentication token"""
        login_payload = {
            "email": current_app.config['BOSTA_EMAIL'],
            "password": current_app.config['BOSTA_PASSWORD']
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/users/login",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=login_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('data', {}).get('token'):
                    self.fail(f"No token in response: {data}")
                
                # Get the raw token and clean it up
                raw_token = data['data']['token']
                # Remove 'Bearer' and any extra spaces
                token = raw_token.replace('Bearer', '').strip()
                
                # Log success for debugging
                print(f"\nSuccessfully got token for email: {login_payload['email']}")
                return token
            else:
                self.fail(f"Login failed with status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.fail(f"Error getting token: {str(e)}")
            return None
    
    def test_login_api(self):
        """Test the login API to get authentication token"""
        login_payload = {
            "email": os.getenv('BOSTA_EMAIL'),
            "password": os.getenv('BOSTA_PASSWORD')
        }
        
        response = requests.post(
            f"{self.base_url}/users/login",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=login_payload
        )
        
        print("\nLogin API Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print("\nResponse Data:")
        print(response.text)
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data.get('success'))
        self.assertIn('token', response_data.get('data', {}))
        
        token = response_data['data']['token']
        print(f"\nToken: {token}")
        
        # Test the token with a simple API call
        test_response = requests.get(
            f"{self.base_url}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"\nTest API Response:")
        print(f"Status Code: {test_response.status_code}")
        print(f"Response: {test_response.text}")
        
        return token

    def test_create_pickup(self):
        """Test creating a pickup request"""
        # Initialize test instance variables
        self.current_pickup_id = None

        # Get fresh token
        token = self.get_token()
        self.service.token = token
        self.service.headers["Authorization"] = f"Bearer {token}"

        # Calculate next business day (skip Fridays)
        pickup_date = datetime.now() + timedelta(days=1)
        while pickup_date.weekday() == 4:  # Skip Fridays
            pickup_date += timedelta(days=1)

        # Format date for API
        formatted_date = pickup_date.strftime("%Y-%m-%d")

        # Get default location first
        locations_response = requests.get(
            f"{self.base_url}/pickup-locations",
            headers=self.headers
        )

        self.assertEqual(locations_response.status_code, 200, "Failed to get pickup locations")
        locations = locations_response.json()['data']['list']
        self.assertTrue(locations, "No pickup locations found")

        default_location = locations[0]

        # First check if there's an existing pickup for this date
        query_params = {
            "locationId": default_location['_id'],
            "date": formatted_date,
            "page": 1,
            "limit": 10,
            "status": "REQUESTED,CONFIRMED"  # Only get active pickups
        }

        existing_pickups_response = requests.get(
            f"{self.base_url}/pickups",
            headers=self.headers,
            params=query_params
        )

        if existing_pickups_response.status_code == 200:
            existing_pickups = existing_pickups_response.json()
            if existing_pickups.get('data', {}).get('list'):
                # Use existing pickup
                self.current_pickup_id = existing_pickups['data']['list'][0]['_id']
                print(f"\nUsing existing pickup with ID: {self.current_pickup_id}")
                return self.current_pickup_id

        # Create new pickup request if none exists
        pickup_payload = {
            "scheduledDate": formatted_date,
            "scheduledTimeSlot": "10:00 to 13:00",
            "locationId": default_location['_id'],
            "type": "Business Pickup",
            "notes": "Test pickup from API flow",
            "businessReference": "test_pickup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        }

        try:
            response = requests.post(
                f"{self.base_url}/pickups",
                headers=self.headers,
                json=pickup_payload
            )

            if response.status_code == 400 and "Cannot create two pickup requests" in response.text:
                # Double check for existing pickups again
                existing_pickups_response = requests.get(
                    f"{self.base_url}/pickups",
                    headers=self.headers,
                    params=query_params
                )
                
                if existing_pickups_response.status_code == 200:
                    existing_pickups = existing_pickups_response.json()
                    if existing_pickups.get('data', {}).get('list'):
                        self.current_pickup_id = existing_pickups['data']['list'][0]['_id']
                        print(f"\nUsing existing pickup with ID: {self.current_pickup_id}")
                        return self.current_pickup_id
                
                self.fail("Failed to create pickup and no existing pickup found")

            self.assertEqual(response.status_code, 200, f"Failed to create pickup: {response.text}")
            
            pickup_data = response.json()['data']
            self.current_pickup_id = pickup_data['_id']
            
            print(f"\nCreated new pickup with ID: {self.current_pickup_id}")
            return self.current_pickup_id

        except Exception as e:
            self.fail(f"Error creating pickup: {str(e)}")

    def test_create_delivery(self):
        """Test creating a delivery order"""
        # Initialize test instance variables
        self.current_tracking_number = None

        # First create a pickup if we don't have one
        if not hasattr(self, 'current_pickup_id'):
            self.test_create_pickup()

        if not hasattr(self, 'headers'):
            token = self.get_token()
            self.headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": token
            }

        # Get default location
        locations_response = requests.get(
            f"{self.base_url}/pickup-locations",
            headers=self.headers
        )

        self.assertEqual(locations_response.status_code, 200, "Failed to get pickup locations")
        locations = locations_response.json()['data']['list']
        self.assertTrue(locations, "No pickup locations found")
        default_location = locations[0]

        delivery_payload = {
            "type": 10,
            "specs": {
                "packageType": "Parcel",
                "size": "MEDIUM",
                "packageDetails": {
                    "itemsCount": 1,
                    "description": "Test package"
                }
            },
            "notes": "Test delivery from API flow",
            "cod": 100,
            "dropOffAddress": {
                "city": "Cairo",
                "firstLine": "Test Delivery Address",
                "secondLine": "API Flow Test",
                "buildingNumber": "123",
                "floor": "1",
                "apartment": "1"
            },
            "pickupAddress": {
                "city": default_location['address'].get('city', {}).get('name', 'Cairo'),
                "firstLine": default_location['address']['firstLine'],
                "secondLine": default_location['address'].get('secondLine', ''),
                "buildingNumber": default_location['address'].get('buildingNumber', ''),
                "floor": default_location['address'].get('floor', ''),
                "apartment": default_location['address'].get('apartment', '')
            },
            "businessReference": f"TEST-FLOW-{int(time.time())}",
            "receiver": {
                "firstName": "Test",
                "lastName": "Receiver",
                "phone": "01001001000",
                "email": "test@example.com"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/deliveries",
                headers=self.headers,
                json=delivery_payload
            )

            self.assertIn(response.status_code, [200, 201], f"Failed to create delivery: {response.text}")
            
            delivery_data = response.json()['data']
            self.current_tracking_number = delivery_data['trackingNumber']
            
            print(f"\nCreated delivery with tracking number: {self.current_tracking_number}")
            return self.current_tracking_number

        except Exception as e:
            self.fail(f"Error creating delivery: {str(e)}")

    def test_complete_shipping_flow(self):
        """Test complete shipping flow: Create Pickup -> Create Delivery"""
        # Initialize test instance variables
        self.current_pickup_id = None
        self.current_tracking_number = None
        
        print("\nStarting Complete Shipping Flow Test")
        
        # Step 1: Create pickup
        pickup_id = self.test_create_pickup()
        self.assertIsNotNone(pickup_id)
        print(f"\n[OK] Created/Found pickup: {pickup_id}")
        
        # Step 2: Create delivery
        tracking_number = self.test_create_delivery()
        self.assertIsNotNone(tracking_number)
        print(f"[OK] Created delivery: {tracking_number}")
        
        print("\nComplete Shipping Flow Test Finished Successfully!")
        print(f"Summary:")
        print(f"- Pickup ID: {pickup_id}")
        print(f"- Tracking Number: {tracking_number}")
        
        # Get default location info
        locations_response = requests.get(
            f"{self.base_url}/pickup-locations",
            headers=self.headers
        )
        if locations_response.status_code == 200:
            locations = locations_response.json()['data']['list']
            if locations:
                default_location = locations[0]
                print(f"- Location: {default_location['locationName']}")
        
        return tracking_number

    def test_complete_flow_with_token(self):
        """Test the complete shipping flow using fresh token"""
        print("\nStarting Complete Flow Test with Token")
        
        # Initialize test instance variables for cleanup
        self.current_tracking_number = None
        self.current_pickup_id = None
        
        # Step 1: Get fresh token
        login_payload = {
            "email": os.getenv('BOSTA_EMAIL'),
            "password": os.getenv('BOSTA_PASSWORD')
        }
        
        login_response = requests.post(
            f"{self.base_url}/users/login",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=login_payload
        )
        
        self.assertEqual(login_response.status_code, 200, "Login failed")
        token = login_response.json()['data']['token']
        print("[OK] Login successful")
        
        # Update headers with fresh token
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": token
        }
        
        # Step 2: Get pickup locations
        locations_response = requests.get(
            f"{self.base_url}/pickup-locations",
            headers=self.headers
        )
        
        self.assertEqual(locations_response.status_code, 200, "Failed to get pickup locations")
        response_data = locations_response.json()
        print(f"\nPickup Locations Response:")
        print(json.dumps(response_data, indent=2))
        
        # Get locations list from the nested structure
        locations = response_data.get('data', {}).get('list', [])
        if not locations:
            self.fail("No pickup locations found in response")
            
        # Try to find default location or use first available
        default_location = None
        for loc in locations:
            if loc.get('isDefault'):
                default_location = loc
                break
        
        if not default_location and locations:
            default_location = locations[0]
            
        if not default_location:
            self.fail("No valid pickup location found")
            
        print(f"[OK] Got pickup location: {default_location['locationName']}")
        
        # Step 3: Create pickup or use existing one
        # Calculate next business day (skip Fridays)
        pickup_date = datetime.now() + timedelta(days=1)
        while pickup_date.weekday() == 4:  # 4 is Friday
            pickup_date += timedelta(days=1)
            
        pickup_payload = {
            "scheduledDate": pickup_date.strftime("%Y-%m-%d"),
            "scheduledTimeSlot": "10:00 to 13:00",
            "locationId": default_location['_id'],
            "notes": "Test pickup from API flow"
        }
        
        print(f"[INFO] Attempting pickup for: {pickup_payload['scheduledDate']} at {pickup_payload['scheduledTimeSlot']}")
        
        pickup_response = requests.post(
            f"{self.base_url}/pickups",
            headers=self.headers,
            json=pickup_payload
        )
        
        # Check pickup response
        pickup_data = pickup_response.json()
        
        if pickup_response.status_code == 200 and pickup_data.get('success'):
            # New pickup created successfully
            self.current_pickup_id = pickup_data['data']['_id']
            print(f"[OK] Created new pickup with ID: {self.current_pickup_id}")
        elif (pickup_response.status_code == 400 and 
              pickup_data.get('errorCode') == 1078 and 
              "Cannot create two pickup requests at the same date and pickup location" in pickup_data.get('message', '')):
            # Pickup already exists for this date/location - this is fine
            print(f"[OK] Using existing pickup for date {pickup_payload['scheduledDate']}")
            
            # Get existing pickups to find the ID
            query_params = {
                "locationId": default_location['_id'],
                "date": pickup_payload['scheduledDate'],
                "page": 1,
                "limit": 10,
                "status": "REQUESTED,CONFIRMED"  # Only get active pickups
            }
            
            existing_pickups_response = requests.get(
                f"{self.base_url}/pickups",
                headers=self.headers,
                params=query_params
            )
            
            if existing_pickups_response.status_code == 200:
                existing_data = existing_pickups_response.json()
                print("\nExisting Pickups Response:")
                print(json.dumps(existing_data, indent=2))
                
                pickups_list = existing_data.get('data', {}).get('list', [])
                matching_pickup = None
                
                # Find pickup for our date
                target_date = pickup_date.strftime("%m-%d-%Y")
                for pickup in pickups_list:
                    scheduled_date = pickup.get('scheduledDate', '').split(',')[0]  # Format: "12-14-2024, 03:00:00"
                    if scheduled_date == target_date:
                        matching_pickup = pickup
                        break
                
                if matching_pickup:
                    self.current_pickup_id = matching_pickup['_id']
                    print(f"[INFO] Found existing pickup ID: {self.current_pickup_id}")
                else:
                    self.fail("No matching pickup found for the target date")
            else:
                print("\nFailed to retrieve existing pickups:")
                print(json.dumps(existing_pickups_response.json(), indent=2))
                self.fail("Failed to retrieve existing pickups")
        else:
            # Actual error occurred
            print(f"\nPickup Creation Error Response:")
            print(json.dumps(pickup_data, indent=2))
            self.fail(f"Failed to create pickup. Status: {pickup_response.status_code}")
        
        # Step 4: Create delivery
        delivery_payload = {
            "type": 10,
            "specs": {
                "packageType": "Parcel",
                "size": "MEDIUM",
                "packageDetails": {
                    "itemsCount": 1,
                    "description": "Test package from flow"
                }
            },
            "notes": "Test delivery from API flow",
            "cod": 100,
            "dropOffAddress": {
                "city": "Cairo",
                "firstLine": "Test Delivery Address",
                "secondLine": "API Flow Test",
                "buildingNumber": "123",
                "floor": "1",
                "apartment": "1"
            },
            "pickupAddress": {
                "city": default_location['address'].get('city', {}).get('name', 'Cairo'),
                "firstLine": default_location['address']['firstLine'],
                "secondLine": default_location['address'].get('secondLine', ''),
                "buildingNumber": default_location['address'].get('buildingNumber', ''),
                "floor": default_location['address'].get('floor', ''),
                "apartment": default_location['address'].get('apartment', '')
            },
            "businessReference": f"TEST-FLOW-{int(time.time())}",
            "receiver": {
                "firstName": "Test",
                "lastName": "Receiver",
                "phone": "01001001000",
                "email": "test@example.com"
            }
        }
        
        delivery_response = requests.post(
            f"{self.base_url}/deliveries",
            headers=self.headers,
            json=delivery_payload
        )
        
        # Check for successful delivery creation (both 200 and 201 are valid)
        if delivery_response.status_code not in [200, 201]:
            print(f"\nDelivery Creation Error Response:")
            print(json.dumps(delivery_response.json(), indent=2))
            self.fail(f"Failed to create delivery. Status: {delivery_response.status_code}")
            
        delivery_data = delivery_response.json()
        
        # Verify the delivery was created successfully
        self.assertTrue(delivery_data.get('success'), "Delivery creation response indicates failure")
        self.assertIn('trackingNumber', delivery_data.get('data', {}), "No tracking number in response")
        
        self.current_tracking_number = delivery_data['data']['trackingNumber']
        print(f"[OK] Created delivery with tracking number: {self.current_tracking_number}")
        print(f"[INFO] Delivery state: {delivery_data['data']['state']['value']}")
        
        print("\nComplete Flow Test Finished Successfully!")
        print(f"Summary:")
        print(f"- Pickup ID: {self.current_pickup_id}")
        print(f"- Tracking Number: {self.current_tracking_number}")
        print(f"- Location: {default_location['locationName']}")
        print(f"- Current State: {delivery_data['data']['state']['value']}")

    def test_get_default_location(self):
        """Test retrieving default pickup location"""
        # Get fresh token
        token = self.get_token()
        self.service.token = token
        self.service.headers["Authorization"] = f"Bearer {token}"
        
        try:
            response = requests.get(
                f"{self.base_url}/pickup-locations",
                headers=self.headers
            )
            
            self.assertEqual(response.status_code, 200, f"Failed to get locations. Status: {response.status_code}, Response: {response.text}")
            
            data = response.json()
            self.assertIn('data', data)
            
            # Check that data contains list field
            self.assertIn('list', data['data'], "Response data missing 'list' field")
            locations = data['data']['list']
            self.assertIsInstance(locations, list, "'data.list' should be a list of locations")
            self.assertGreater(len(locations), 0, "No locations found")
            
            # Print the first location for debugging
            if locations:
                print("\nFirst Location Details:")
                print(json.dumps(locations[0], indent=2))
                
                # Verify location structure
                first_location = locations[0]
                self.assertIn('address', first_location, "Location missing 'address' field")
                address = first_location['address']
                
                # Print address details
                print("\nAddress Details:")
                print(f"City: {address.get('city', {}).get('name', 'N/A')}")
                print(f"First Line: {address.get('firstLine', 'N/A')}")
                print(f"Building Number: {address.get('buildingNumber', 'N/A')}")
                print(f"Floor: {address.get('floor', 'N/A')}")
                print(f"Apartment: {address.get('apartment', 'N/A')}")
                
        except Exception as e:
            self.fail(f"Error getting default location: {str(e)}")

    def test_city_validation(self):
        """Test city name validation and normalization"""
        # Test valid cities
        self.assertEqual(BostaCityMapping.normalize_name('Cairo'), 'Cairo')
        self.assertEqual(BostaCityMapping.get_code('Cairo'), 'EG-01')
        
        self.assertEqual(BostaCityMapping.normalize_name('القاهرة'), 'Cairo')
        self.assertEqual(BostaCityMapping.get_code('القاهرة'), 'EG-01')
        
        self.assertEqual(BostaCityMapping.normalize_name('Minya'), 'Menya')
        self.assertEqual(BostaCityMapping.get_code('Minya'), 'EG-19')
        
        # Test case insensitivity
        self.assertEqual(BostaCityMapping.normalize_name('cairo'), 'Cairo')
        self.assertEqual(BostaCityMapping.get_code('cairo'), 'EG-01')
        
        self.assertEqual(BostaCityMapping.normalize_name('ALEXANDRIA'), 'Alexandria')
        self.assertEqual(BostaCityMapping.get_code('ALEXANDRIA'), 'EG-02')
        
        # Test invalid cities
        self.assertIsNone(BostaCityMapping.normalize_name('Invalid City'))
        self.assertIsNone(BostaCityMapping.get_code('Invalid City'))
        
        self.assertIsNone(BostaCityMapping.normalize_name(''))
        self.assertIsNone(BostaCityMapping.get_code(''))
        
        self.assertIsNone(BostaCityMapping.normalize_name(None))
        self.assertIsNone(BostaCityMapping.get_code(None))

    def test_shipping_cost_calculation(self):
        """Test shipping cost calculation with city validation"""
        # Get fresh token
        token = self.get_token()
        self.service.token = token
        self.service.headers["Authorization"] = f"Bearer {token}"
        
        # Test with valid cities
        address = Address(
            name="Test User",
            phone="1234567890",
            street="Test Street",
            building_number="123",
            floor="1",
            apartment="2",
            city="Cairo",
            district="Test District",
            user_id=1  # Required for the foreign key constraint
        )
        
        # Calculate shipping cost
        cost = self.service.estimate_shipping_cost('Cairo', 'Alexandria', cod_amount=100)
        self.assertIsNotNone(cost)
        self.assertIsInstance(cost, dict)
        self.assertIn('data', cost)
        
        # Print response for debugging
        print("\nShipping Cost Response:")
        print(json.dumps(cost, indent=2))
        
        # Test with invalid cities
        cost = self.service.estimate_shipping_cost('InvalidCity', 'Alexandria')
        self.assertIsNone(cost)

    def test_estimate_shipping_cost(self):
        """Test shipping cost estimation"""
        # Get fresh token
        token = self.get_token()
        self.service.token = token
        self.service.headers["Authorization"] = f"Bearer {token}"
        
        # Test with valid cities
        cost = self.service.estimate_shipping_cost('Cairo', 'Alexandria', cod_amount=100)
        self.assertIsNotNone(cost)
        self.assertIsInstance(cost, dict)
        self.assertIn('data', cost)
        
        # Print response for debugging
        print("\nShipping Cost Response:")
        print(json.dumps(cost, indent=2))
        
        # Test with invalid cities
        cost = self.service.estimate_shipping_cost('InvalidCity', 'Alexandria')
        self.assertIsNone(cost)

    def test_shipping_cost_api_response(self):
        """Test detailed shipping cost API response structure"""
        service = BostaShippingService()
        
        # Set up the token properly
        token = self.get_token()
        service.token = token
        service.headers["Authorization"] = f"Bearer {token}"
        
        # Get shipping cost estimate
        cost = service.estimate_shipping_cost('Cairo', 'Ismailia', cod_amount=100)
        
        # Verify response structure
        self.assertIsInstance(cost, dict)
        self.assertIn('data', cost)
        self.assertIn('success', cost)
        self.assertTrue(cost['success'])

        data = cost['data']
        self.assertIn('tier', data)
        tier = data['tier']
        
        # Check tier structure
        self.assertIn('cost', tier)
        self.assertIn('codFee', tier)
        self.assertIn('bostaMaterialFee', tier)
        self.assertIn('openingPackageFee', tier)
        
        # Verify the cost components exist
        self.assertIsInstance(tier['cost'], (int, float))
        self.assertIsInstance(tier['codFee'].get('amount', 0), (int, float))
        self.assertIsInstance(tier['bostaMaterialFee'].get('amount', 0), (int, float))
        self.assertIsInstance(tier['openingPackageFee'].get('amount', 0), (int, float))
        
    def test_estimate_shipping_cost(self):
        """Test shipping cost estimation"""
        # Get fresh token
        token = self.get_token()
        self.service.token = token
        self.service.headers["Authorization"] = f"Bearer {token}"
        
        # Test with valid cities
        cost = self.service.estimate_shipping_cost('Cairo', 'Alexandria', cod_amount=100)
        self.assertIsNotNone(cost)
        self.assertIsInstance(cost, dict)
        self.assertIn('data', cost)
        
        # Print response for debugging
        print("\nShipping Cost Response:")
        print(json.dumps(cost, indent=2))
        
        # Test with invalid cities
        cost = self.service.estimate_shipping_cost('InvalidCity', 'Alexandria')
        self.assertIsNone(cost)

if __name__ == '__main__':
    unittest.main()
