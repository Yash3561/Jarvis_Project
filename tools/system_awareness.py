# tools/system_awareness.py
import requests
import geocoder

def get_location() -> str:
    """
    Fetches the user's current city and country based on their IP address.
    This provides essential context for location-based queries like weather.
    Returns a string like 'City, Country'.
    """
    try:
        # First, try the geocoder library which is often more reliable
        g = geocoder.ip('me')
        if g.ok:
            return f"{g.city}, {g.country}"
        
        # Fallback to a public API if geocoder fails
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        city = data.get('city', 'Unknown')
        country = data.get('country', 'Unknown')
        return f"{city}, {country}"
    except Exception as e:
        print(f"ERROR: Could not fetch location: {e}")
        return "Error fetching location. Could not determine the user's location."