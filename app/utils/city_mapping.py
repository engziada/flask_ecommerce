"""
City mapping utilities for shipping services.
This module provides city code mappings for various shipping carriers.
"""

class BostaCityMapping:
    """
    Maps city names to Bosta city codes.
    Used for shipping cost calculations and address validation.
    """
    
    # Mapping of city names to Bosta city codes
    CITY_MAPPING = {
        'Cairo': 'CAI',
        'Alexandria': 'ALX',
        'Giza': 'GIZ',
        'Port Said': 'PSD',
        'Suez': 'SUZ',
        'Luxor': 'LXR',
        'Aswan': 'ASW',
        'Ismailia': 'ISM',
        'Hurghada': 'HRG',
        'Sharm El Sheikh': 'SSH',
        'Mansoura': 'MNS',
        'Tanta': 'TNT',
        'Damietta': 'DMT',
        'Fayoum': 'FYM',
        'Zagazig': 'ZAG',
        'Asyut': 'ASY',
        'Beni Suef': 'BSF',
        'Sohag': 'SOH',
        'Qena': 'QEN',
        'Minya': 'MNA'
    }

    @classmethod
    def get_code(cls, city_name):
        """Get the Bosta city code for a given city name"""
        return cls.CITY_MAPPING.get(city_name)

    @classmethod
    def get_city_choices(cls):
        """Get list of city choices for forms"""
        return sorted(cls.CITY_MAPPING.keys())
