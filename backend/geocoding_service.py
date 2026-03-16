"""
Geocoding service for converting location text to coordinates.
Uses a simple in-memory cache for common locations.
"""

from typing import Dict, Tuple, Optional


class GeocodingService:
    """
    Simple geocoding service with common locations.
    
    For production, integrate with:
    - Google Maps Geocoding API
    - Mapbox Geocoding API
    - Or similar service
    """
    
    # Common locations cache (city -> (lat, lon))
    LOCATIONS = {
        "melbourne, australia": (-37.8136, 144.9631),
        "melbourne": (-37.8136, 144.9631),
        "sydney, australia": (-33.8688, 151.2093),
        "sydney": (-33.8688, 151.2093),
        "brisbane, australia": (-27.4698, 153.0251),
        "brisbane": (-27.4698, 153.0251),
        "perth, australia": (-31.9505, 115.8605),
        "perth": (-31.9505, 115.8605),
        "adelaide, australia": (-34.9285, 138.6007),
        "adelaide": (-34.9285, 138.6007),
        "london": (51.5074, -0.1278),
        "london, uk": (51.5074, -0.1278),
        "new york": (40.7128, -74.0060),
        "new york, ny": (40.7128, -74.0060),
        "los angeles": (34.0522, -118.2437),
        "los angeles, ca": (34.0522, -118.2437),
        "san francisco": (37.7749, -122.4194),
        "san francisco, ca": (37.7749, -122.4194),
        "chicago": (41.8781, -87.6298),
        "chicago, il": (41.8781, -87.6298),
        "tokyo": (35.6762, 139.6503),
        "tokyo, japan": (35.6762, 139.6503),
        "paris": (48.8566, 2.3522),
        "paris, france": (48.8566, 2.3522),
        "berlin": (52.5200, 13.4050),
        "berlin, germany": (52.5200, 13.4050),
        "toronto": (43.6532, -79.3832),
        "toronto, canada": (43.6532, -79.3832),
        "vancouver": (49.2827, -123.1207),
        "vancouver, canada": (49.2827, -123.1207),
    }
    
    def __init__(self):
        """Initialize geocoding service."""
        pass
    
    def geocode(self, location_text: str) -> Optional[Tuple[float, float]]:
        """
        Convert location text to coordinates.
        
        Args:
            location_text: Location string (e.g., "Melbourne, Australia")
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Normalize input
        normalized = location_text.lower().strip()
        
        # Check cache
        if normalized in self.LOCATIONS:
            return self.LOCATIONS[normalized]
        
        # For MVP, return None if not in cache
        # In production, call external geocoding API here
        return None

    def suggest_locations(self, query: str, limit: int = 6) -> list[Dict[str, str]]:
        """
        Return location suggestions based on prefix match in the cache.

        Args:
            query: Partial location string
            limit: Max suggestions
        """
        normalized_query = query.lower().strip()
        if not normalized_query:
            return []

        results = []
        for key in self.LOCATIONS.keys():
            if key.startswith(normalized_query):
                label = ", ".join([part.strip().title() for part in key.split(",")])
                results.append({
                    "label": label,
                    "normalized": key,
                    "verified": True
                })
            if len(results) >= limit:
                break

        return results
    
    def geocode_with_fallback(
        self, 
        location_text: str,
        fallback: Tuple[float, float] = (0.0, 0.0)
    ) -> Tuple[float, float]:
        """
        Geocode with fallback to default coordinates.
        
        Args:
            location_text: Location string
            fallback: Default coordinates if geocoding fails
            
        Returns:
            Tuple of (latitude, longitude)
        """
        result = self.geocode(location_text)
        if result is None:
            return fallback
        return result


# Singleton instance
_geocoding_service = None

def get_geocoding_service() -> GeocodingService:
    """Get or create singleton geocoding service instance."""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service
