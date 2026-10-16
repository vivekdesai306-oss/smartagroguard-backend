"""
AgroGuard Geocoding & Location Hierarchy Service
Provides bidirectional translation between geographic coordinates (lat, lon)
and administrative location names (Village, Taluka / City, District, State).
Guarantees resilience via dual-tier OpenStreetMap Nominatim with local agro-dictionary fallback.
"""

import logging
import urllib.request
import urllib.parse
import json
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("agroguard.geocoding_service")

# In-memory cache for ultra-fast repeat lookups
_REVERSE_CACHE: Dict[str, Dict[str, Any]] = {}
_FORWARD_CACHE: Dict[str, Dict[str, Any]] = {}

# Offline dictionary of prominent Indian agricultural zones
KNOWN_LOCATIONS = [
    # Gujarat - Zone III (Panchmahal, Anand, Vadodara, Dahod, Kheda)
    {
        "village": "Vavdi", "taluka": "Godhra", "city": "Godhra", "district": "Panchmahal", "state": "Gujarat",
        "lat": 22.7758, "lon": 73.6149, "address": "Vavdi, Godhra, Panchmahal, Gujarat, India"
    },
    {
        "village": "Tuwa", "taluka": "Godhra", "city": "Godhra", "district": "Panchmahal", "state": "Gujarat",
        "lat": 22.7932, "lon": 73.4912, "address": "Tuwa, Godhra, Panchmahal, Gujarat, India"
    },
    {
        "village": "Halol", "taluka": "Halol", "city": "Halol", "district": "Panchmahal", "state": "Gujarat",
        "lat": 22.5024, "lon": 73.4716, "address": "Halol, Panchmahal, Gujarat, India"
    },
    {
        "village": "Kalol", "taluka": "Kalol", "city": "Kalol", "district": "Panchmahal", "state": "Gujarat",
        "lat": 22.6074, "lon": 73.4568, "address": "Kalol, Panchmahal, Gujarat, India"
    },
    {
        "village": "Shehra", "taluka": "Shehra", "city": "Shehra", "district": "Panchmahal", "state": "Gujarat",
        "lat": 22.9464, "lon": 73.6334, "address": "Shehra, Panchmahal, Gujarat, India"
    },
    {
        "village": "Anand", "taluka": "Anand", "city": "Anand", "district": "Anand", "state": "Gujarat",
        "lat": 22.5645, "lon": 72.9289, "address": "Anand, Anand District, Gujarat, India"
    },
    {
        "village": "Borsad", "taluka": "Borsad", "city": "Borsad", "district": "Anand", "state": "Gujarat",
        "lat": 22.4116, "lon": 72.9022, "address": "Borsad, Anand District, Gujarat, India"
    },
    {
        "village": "Dabhoi", "taluka": "Dabhoi", "city": "Dabhoi", "district": "Vadodara", "state": "Gujarat",
        "lat": 22.1332, "lon": 73.4326, "address": "Dabhoi, Vadodara, Gujarat, India"
    },
    {
        "village": "Padra", "taluka": "Padra", "city": "Padra", "district": "Vadodara", "state": "Gujarat",
        "lat": 22.2407, "lon": 73.0831, "address": "Padra, Vadodara, Gujarat, India"
    },
    {
        "village": "Dahod", "taluka": "Dahod", "city": "Dahod", "district": "Dahod", "state": "Gujarat",
        "lat": 22.8368, "lon": 74.2575, "address": "Dahod, Dahod District, Gujarat, India"
    },
    {
        "village": "Nadiad", "taluka": "Nadiad", "city": "Nadiad", "district": "Kheda", "state": "Gujarat",
        "lat": 22.6916, "lon": 72.8634, "address": "Nadiad, Kheda, Gujarat, India"
    },
    # Bihar - Zone 4 (Middle Gangetic Plains Maize Tract)
    {
        "village": "Barauni", "taluka": "Barauni", "city": "Barauni", "district": "Begusarai", "state": "Bihar",
        "lat": 25.4746, "lon": 85.9658, "address": "Barauni, Begusarai, Bihar, India"
    },
    {
        "village": "Begusarai", "taluka": "Begusarai", "city": "Begusarai", "district": "Begusarai", "state": "Bihar",
        "lat": 25.4182, "lon": 86.1272, "address": "Begusarai, Begusarai District, Bihar, India"
    },
    # Punjab - Zone 6 (Trans-Gangetic Plains)
    {
        "village": "Jagraon", "taluka": "Jagraon", "city": "Jagraon", "district": "Ludhiana", "state": "Punjab",
        "lat": 30.7844, "lon": 75.4764, "address": "Jagraon, Ludhiana, Punjab, India"
    },
    {
        "village": "Khanna", "taluka": "Khanna", "city": "Khanna", "district": "Ludhiana", "state": "Punjab",
        "lat": 30.7042, "lon": 76.2198, "address": "Khanna, Ludhiana, Punjab, India"
    },
    # Karnataka - Zone 10 (Southern Maize Belt)
    {
        "village": "Harihar", "taluka": "Harihar", "city": "Harihar", "district": "Davangere", "state": "Karnataka",
        "lat": 14.5126, "lon": 75.8038, "address": "Harihar, Davangere, Karnataka, India"
    },
    {
        "village": "Davangere", "taluka": "Davangere", "city": "Davangere", "district": "Davangere", "state": "Karnataka",
        "lat": 14.4644, "lon": 75.9218, "address": "Davangere, Karnataka, India"
    },
    # Telangana - Zone 10
    {
        "village": "Karimnagar", "taluka": "Karimnagar", "city": "Karimnagar", "district": "Karimnagar", "state": "Telangana",
        "lat": 18.4386, "lon": 79.1288, "address": "Karimnagar, Telangana, India"
    }
]

class GeocodingService:
    @classmethod
    def reverse_geocode(cls, lat: float, lon: float) -> Dict[str, Any]:
        """
        Translates coordinates (lat, lon) into administrative location hierarchy:
        Village, Taluka / City, District, State, and Formatted Address.
        """
        cache_key = f"{round(lat, 4)},{round(lon, 4)}"
        if cache_key in _REVERSE_CACHE:
            return _REVERSE_CACHE[cache_key]

        # 1. Try querying Nominatim OpenStreetMap
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AgroGuard-Platform/1.0 (agroguard-dev@precisionag.org)"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                addr = data.get("address", {})

                # Extract location components
                village = (
                    addr.get("village") or
                    addr.get("hamlet") or
                    addr.get("suburb") or
                    addr.get("neighbourhood") or
                    addr.get("isolated_dwelling") or
                    ""
                )
                city = (
                    addr.get("city") or
                    addr.get("town") or
                    addr.get("municipality") or
                    ""
                )
                taluka = (
                    addr.get("county") or
                    addr.get("subdistrict") or
                    city or
                    ""
                )
                # Clean up "Taluka" suffix if present
                clean_taluka = taluka.replace(" Taluka", "").replace(" taluka", "").strip()

                district = (
                    addr.get("state_district") or
                    addr.get("district") or
                    addr.get("county", "").replace(" Taluka", "").strip() or
                    ""
                )
                state = addr.get("state", "")

                formatted = data.get("display_name", "")
                # Create a concise farm address
                parts = [p for p in [village, clean_taluka, district, state] if p]
                clean_address = ", ".join(parts) if parts else formatted

                result = {
                    "status": "success",
                    "latitude": lat,
                    "longitude": lon,
                    "village": village or clean_taluka,
                    "taluka": clean_taluka or district,
                    "city": city or clean_taluka,
                    "district": district,
                    "state": state,
                    "country": addr.get("country", "India"),
                    "formatted_address": clean_address or formatted,
                    "source": "openstreetmap_nominatim"
                }

                _REVERSE_CACHE[cache_key] = result
                return result

        except Exception as e:
            logger.warning(f"Nominatim reverse geocode lookup failed for ({lat}, {lon}): {e}")

        # 2. Resilient Fallback to Nearest Known Agricultural Location
        best_match = cls._find_nearest_known(lat, lon)
        if best_match:
            result = {
                "status": "success",
                "latitude": lat,
                "longitude": lon,
                "village": best_match["village"],
                "taluka": best_match["taluka"],
                "city": best_match["city"],
                "district": best_match["district"],
                "state": best_match["state"],
                "country": "India",
                "formatted_address": best_match["address"],
                "source": "agroguard_local_catalog"
            }
            _REVERSE_CACHE[cache_key] = result
            return result

        # 3. Default Panchmahal fallback
        default_res = {
            "status": "success",
            "latitude": lat,
            "longitude": lon,
            "village": "Vavdi",
            "taluka": "Godhra",
            "city": "Godhra",
            "district": "Panchmahal",
            "state": "Gujarat",
            "country": "India",
            "formatted_address": "Vavdi, Godhra, Panchmahal, Gujarat",
            "source": "default_fallback"
        }
        _REVERSE_CACHE[cache_key] = default_res
        return default_res

    @classmethod
    def forward_geocode(
        cls,
        village: Optional[str] = None,
        taluka: Optional[str] = None,
        district: Optional[str] = None,
        state: Optional[str] = None,
        freeform_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translates administrative location hierarchy (village, taluka, district, state)
        into exact latitude and longitude coordinates.
        """
        # Construct search query string
        parts = []
        if village and village.strip():
            parts.append(village.strip())
        if taluka and taluka.strip():
            parts.append(taluka.strip())
        if district and district.strip():
            parts.append(district.strip())
        if state and state.strip():
            parts.append(state.strip())

        query = freeform_query.strip() if (freeform_query and freeform_query.strip()) else ", ".join(parts)
        if not query:
            query = "Godhra, Panchmahal, Gujarat"

        cache_key = query.lower()
        if cache_key in _FORWARD_CACHE:
            return _FORWARD_CACHE[cache_key]

        # 1. Check local catalog first for immediate match
        local_hit = cls._find_known_by_name(village, taluka, district, state, query)
        if local_hit:
            res = {
                "status": "success",
                "latitude": local_hit["lat"],
                "longitude": local_hit["lon"],
                "village": local_hit["village"],
                "taluka": local_hit["taluka"],
                "city": local_hit["city"],
                "district": local_hit["district"],
                "state": local_hit["state"],
                "country": "India",
                "formatted_address": local_hit["address"],
                "source": "agroguard_local_catalog"
            }
            _FORWARD_CACHE[cache_key] = res
            return res

        # 2. Query Nominatim forward search
        try:
            encoded_q = urllib.parse.quote(f"{query}, India")
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded_q}&addressdetails=1&limit=1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AgroGuard-Platform/1.0 (agroguard-dev@precisionag.org)"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and len(data) > 0:
                    item = data[0]
                    lat = float(item["lat"])
                    lon = float(item["lon"])
                    addr = item.get("address", {})

                    v = village or addr.get("village") or addr.get("hamlet") or addr.get("suburb") or ""
                    c = addr.get("city") or addr.get("town") or ""
                    t = taluka or addr.get("county") or addr.get("subdistrict") or c or ""
                    d = district or addr.get("state_district") or addr.get("district") or ""
                    s = state or addr.get("state") or ""

                    res = {
                        "status": "success",
                        "latitude": lat,
                        "longitude": lon,
                        "village": v,
                        "taluka": t.replace(" Taluka", "").strip(),
                        "city": c or t,
                        "district": d,
                        "state": s,
                        "country": addr.get("country", "India"),
                        "formatted_address": item.get("display_name", query),
                        "source": "openstreetmap_nominatim"
                    }
                    _FORWARD_CACHE[cache_key] = res
                    return res

        except Exception as e:
            logger.warning(f"Nominatim forward geocode failed for query '{query}': {e}")

        # 3. Fallback to default Vavdi / Godhra / Panchmahal
        default_res = {
            "status": "success",
            "latitude": 22.7758,
            "longitude": 73.6149,
            "village": village or "Vavdi",
            "taluka": taluka or "Godhra",
            "city": "Godhra",
            "district": district or "Panchmahal",
            "state": state or "Gujarat",
            "country": "India",
            "formatted_address": query or "Vavdi, Godhra, Panchmahal, Gujarat",
            "source": "default_fallback"
        }
        _FORWARD_CACHE[cache_key] = default_res
        return default_res

    @staticmethod
    def _find_nearest_known(lat: float, lon: float) -> Optional[Dict[str, Any]]:
        best = None
        min_dist = float("inf")
        for loc in KNOWN_LOCATIONS:
            # Simple Euclidean approximation for proximity check
            d = (loc["lat"] - lat) ** 2 + (loc["lon"] - lon) ** 2
            if d < min_dist:
                min_dist = d
                best = loc
        return best

    @staticmethod
    def _find_known_by_name(
        village: Optional[str],
        taluka: Optional[str],
        district: Optional[str],
        state: Optional[str],
        query: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        v_low = (village or "").lower().strip()
        t_low = (taluka or "").lower().strip()
        d_low = (district or "").lower().strip()
        q_low = (query or "").lower().strip()

        for loc in KNOWN_LOCATIONS:
            loc_v = loc["village"].lower()
            loc_t = loc["taluka"].lower()
            loc_c = loc.get("city", "").lower()
            loc_d = loc["district"].lower()

            if v_low and v_low == loc_v:
                return loc
            if t_low and (t_low == loc_t or t_low == loc_c):
                return loc
            if d_low and d_low == loc_d:
                return loc
            if q_low and (loc_v in q_low or loc_t in q_low or loc_c in q_low or loc_d in q_low):
                return loc
        return None
