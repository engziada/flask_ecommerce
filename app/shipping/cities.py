"""City mappings and validation for Bosta shipping service"""

BOSTA_CITIES = {
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

# Create reverse lookup maps
_CITY_BY_AR = {city_data['ar']: city_name for city_name, city_data in BOSTA_CITIES.items()}
_CITY_BY_ALIAS = {}
for city_name, city_data in BOSTA_CITIES.items():
    if 'aliases' in city_data:
        for alias in city_data['aliases']:
            _CITY_BY_ALIAS[alias] = city_name

def normalize_city_name(city_name):
    """
    Normalize a city name to match Bosta's expected format.
    
    Args:
        city_name (str): Input city name in English, Arabic, or alias form
        
    Returns:
        tuple: (normalized_name, code) if valid city, (None, None) if not found
    """
    if not city_name:
        return None, None
        
    # Clean input
    city_name = city_name.strip()
    
    # Direct match
    if city_name in BOSTA_CITIES:
        return city_name, BOSTA_CITIES[city_name]['code']
        
    # Arabic name match
    if city_name in _CITY_BY_AR:
        normalized = _CITY_BY_AR[city_name]
        return normalized, BOSTA_CITIES[normalized]['code']
        
    # Alias match
    if city_name in _CITY_BY_ALIAS:
        normalized = _CITY_BY_ALIAS[city_name]
        return normalized, BOSTA_CITIES[normalized]['code']
        
    # Case-insensitive match
    city_upper = city_name.upper()
    for valid_name in BOSTA_CITIES:
        if valid_name.upper() == city_upper:
            return valid_name, BOSTA_CITIES[valid_name]['code']
            
    # Check aliases case-insensitive
    for valid_name, data in BOSTA_CITIES.items():
        if 'aliases' in data:
            for alias in data['aliases']:
                if alias.upper() == city_upper:
                    return valid_name, data['code']
                    
    return None, None

def get_city_code(city_name):
    """Get the city code for a given city name"""
    normalized, code = normalize_city_name(city_name)
    return code if code else None

def is_valid_city(city_name):
    """Check if a city name is valid"""
    normalized, _ = normalize_city_name(city_name)
    return normalized is not None
