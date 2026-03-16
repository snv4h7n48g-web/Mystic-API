"""
Astrology calculation engine for natal chart generation.
Provides deterministic sun/moon/rising calculations.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import math


class AstrologyEngine:
    """
    Simplified astrology calculator for MVP.
    
    Note: This is a basic implementation. For production, consider:
    - swiss-ephemeris library (pyswisseph)
    - Proper astronomical calculations
    - House system calculations
    
    This MVP version uses simplified zodiac position calculations.
    """
    
    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", 
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    ELEMENTS = {
        "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
        "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
        "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
        "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
    }
    
    MODALITIES = {
        "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
        "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
        "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"
    }
    
    RULING_PLANETS = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
        "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
        "Libra": "Venus", "Scorpio": "Pluto", "Sagittarius": "Jupiter",
        "Capricorn": "Saturn", "Aquarius": "Uranus", "Pisces": "Neptune"
    }

    CHINESE_ANIMALS = [
        "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
        "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"
    ]

    CHINESE_ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]
    
    def __init__(self):
        """Initialize the astrology engine."""
        pass
    
    def calculate_sun_sign(self, birth_date: str) -> str:
        """
        Calculate sun sign from birth date.
        
        Args:
            birth_date: Date string in format YYYY-MM-DD
            
        Returns:
            Sun sign name
        """
        date = datetime.strptime(birth_date, "%Y-%m-%d")
        month = date.month
        day = date.day
        
        # Simplified zodiac date ranges
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "Capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Aquarius"
        else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
            return "Pisces"
    
    def calculate_moon_sign(
        self, 
        birth_date: str, 
        birth_time: Optional[str] = None
    ) -> Optional[str]:
        """
        Calculate moon sign (simplified).
        
        In production, this requires proper ephemeris data.
        For MVP, we use a placeholder calculation.
        
        Args:
            birth_date: Date string in format YYYY-MM-DD
            birth_time: Optional time string in format HH:MM
            
        Returns:
            Moon sign name or None if time not provided
        """
        if not birth_time:
            return None
        
        # Simplified calculation (placeholder)
        # In production: use pyswisseph or similar
        date = datetime.strptime(birth_date, "%Y-%m-%d")
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        
        # Simplified moon position based on date + time
        # Moon moves ~13 degrees per day through zodiac
        day_of_year = date.timetuple().tm_yday
        moon_position = (day_of_year * 13 + hour * 0.5) % 360
        sign_index = int(moon_position / 30)
        
        return self.ZODIAC_SIGNS[sign_index]
    
    def calculate_rising_sign(
        self,
        birth_date: str,
        birth_time: Optional[str] = None,
        latitude: float = 0.0,
        longitude: float = 0.0
    ) -> Optional[str]:
        """
        Calculate rising sign (ascendant).
        
        Requires birth time and location.
        This is a simplified calculation for MVP.
        
        Args:
            birth_date: Date string in format YYYY-MM-DD
            birth_time: Time string in format HH:MM
            latitude: Birth location latitude
            longitude: Birth location longitude
            
        Returns:
            Rising sign name or None if insufficient data
        """
        if not birth_time:
            return None
        
        # Simplified calculation (placeholder)
        # In production: proper house calculation with pyswisseph
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # Rising sign changes approximately every 2 hours
        # Simplified formula based on local time
        rising_index = (hour // 2) % 12
        
        return self.ZODIAC_SIGNS[rising_index]

    def calculate_chinese_zodiac(self, birth_year: int) -> Dict[str, str]:
        """
        Calculate Chinese zodiac animal + element for a birth year.

        Uses 1924 (Wood Rat) as base year.
        """
        animal_index = (birth_year - 1924) % 12
        element_index = ((birth_year - 1924) % 10) // 2
        animal = self.CHINESE_ANIMALS[animal_index]
        element = self.CHINESE_ELEMENTS[element_index]
        return {
            "animal": animal,
            "element": element,
            "combined": f"{element} {animal}"
        }
    
    def generate_chart(
        self,
        birth_date: str,
        birth_time: Optional[str] = None,
        birth_time_unknown: bool = False,
        latitude: float = 0.0,
        longitude: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate complete natal chart data.
        
        Args:
            birth_date: Birth date (YYYY-MM-DD)
            birth_time: Optional birth time (HH:MM)
            birth_time_unknown: Flag if time is unknown
            latitude: Birth location latitude
            longitude: Birth location longitude
            
        Returns:
            Dict with chart placements and metadata
        """
        sun_sign = self.calculate_sun_sign(birth_date)
        
        # Only calculate moon/rising if time provided
        moon_sign = None
        rising_sign = None
        if birth_time and not birth_time_unknown:
            moon_sign = self.calculate_moon_sign(birth_date, birth_time)
            rising_sign = self.calculate_rising_sign(
                birth_date, birth_time, latitude, longitude
            )
        
        # Determine dominant element
        signs = [sun_sign]
        if moon_sign:
            signs.append(moon_sign)
        if rising_sign:
            signs.append(rising_sign)
        
        element_counts = {}
        for sign in signs:
            element = self.ELEMENTS[sign]
            element_counts[element] = element_counts.get(element, 0) + 1
        
        dominant_element = max(element_counts, key=element_counts.get)
        
        # Determine dominant planet (from sun sign ruler)
        dominant_planet = self.RULING_PLANETS[sun_sign]
        
        # Generate basic aspects (simplified)
        aspects = self._generate_basic_aspects(sun_sign, moon_sign, rising_sign)
        
        return {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "dominant_element": dominant_element,
            "dominant_planet": dominant_planet,
            "sun_element": self.ELEMENTS[sun_sign],
            "sun_modality": self.MODALITIES[sun_sign],
            "top_aspects": aspects,
            "has_time": birth_time is not None and not birth_time_unknown
        }
    
    def _generate_basic_aspects(
        self,
        sun_sign: str,
        moon_sign: Optional[str],
        rising_sign: Optional[str]
    ) -> list[Dict[str, str]]:
        """
        Generate simplified aspect list.
        
        In production, calculate actual angular relationships.
        For MVP, use simplified symbolic relationships.
        
        Args:
            sun_sign: Sun sign
            moon_sign: Moon sign (optional)
            rising_sign: Rising sign (optional)
            
        Returns:
            List of aspect dicts
        """
        aspects = []
        
        if moon_sign:
            # Check if sun and moon are in compatible elements
            sun_element = self.ELEMENTS[sun_sign]
            moon_element = self.ELEMENTS[moon_sign]
            
            if sun_element == moon_element:
                aspects.append({
                    "a": "Sun",
                    "b": "Moon",
                    "type": "Conjunction"
                })
            elif self._are_elements_harmonious(sun_element, moon_element):
                aspects.append({
                    "a": "Sun",
                    "b": "Moon",
                    "type": "Trine"
                })
            else:
                aspects.append({
                    "a": "Sun",
                    "b": "Moon",
                    "type": "Square"
                })
        
        if rising_sign:
            # Sun-Rising aspect
            sun_planet = self.RULING_PLANETS[sun_sign]
            rising_planet = self.RULING_PLANETS[rising_sign]
            
            if sun_planet == "Saturn" or rising_planet == "Saturn":
                aspects.append({
                    "a": "Sun",
                    "b": "Saturn",
                    "type": "Square"
                })
        
        return aspects[:3]  # Return max 3 aspects
    
    def _are_elements_harmonious(self, element1: str, element2: str) -> bool:
        """Check if two elements are harmonious (trine)."""
        harmonious_pairs = [
            {"Fire", "Air"},
            {"Earth", "Water"}
        ]
        return {element1, element2} in harmonious_pairs

    def calculate_synastry(
        self,
        person1_chart: Dict[str, Any],
        person2_chart: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Basic synastry calculation using sign-based angles.
        Returns key aspects and thematic compatibility notes.
        """
        def sign_index(sign: Optional[str]) -> Optional[int]:
            if not sign or sign not in self.ZODIAC_SIGNS:
                return None
            return self.ZODIAC_SIGNS.index(sign)

        def angle_between(a: Optional[str], b: Optional[str]) -> Optional[int]:
            ia = sign_index(a)
            ib = sign_index(b)
            if ia is None or ib is None:
                return None
            diff = abs((ia - ib) * 30) % 360
            return diff if diff <= 180 else 360 - diff

        aspect_map = {
            0: "conjunction",
            60: "sextile",
            90: "square",
            120: "trine",
            180: "opposition"
        }

        def classify_aspect(angle: Optional[int]) -> Optional[str]:
            if angle is None:
                return None
            for key, name in aspect_map.items():
                if abs(angle - key) <= 6:
                    return name
            return None

        pairs = [
            ("Sun", "sun_sign", "Moon", "moon_sign"),
            ("Sun", "sun_sign", "Rising", "rising_sign"),
            ("Moon", "moon_sign", "Moon", "moon_sign"),
            ("Rising", "rising_sign", "Sun", "sun_sign"),
        ]

        aspects = []
        for label_a, key_a, label_b, key_b in pairs:
            a = person1_chart.get(key_a)
            b = person2_chart.get(key_b)
            angle = angle_between(a, b)
            aspect = classify_aspect(angle)
            if a and b and aspect:
                aspects.append({
                    "a": f"Person 1 {label_a}",
                    "b": f"Person 2 {label_b}",
                    "type": aspect,
                    "angle": angle
                })

        return {
            "aspects": aspects
        }


# Singleton instance
_astrology_engine = None

def get_astrology_engine() -> AstrologyEngine:
    """Get or create singleton astrology engine instance."""
    global _astrology_engine
    if _astrology_engine is None:
        _astrology_engine = AstrologyEngine()
    return _astrology_engine
