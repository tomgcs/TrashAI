import json
from io import BytesIO
from typing import Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image

_GPS_IFD_TAG = 0x8825
_GEOSEARCH_URL = "https://geosearch.planninglabs.nyc/v2/search"
_USER_AGENT = "trashai-cuny-aic-2026 (contact: tomgao628@gmail.com)"


def get_location_from_exif(image_bytes: bytes) -> Optional[Tuple[float, float]]:
    try:
        img = Image.open(BytesIO(image_bytes))
        exif = img.getexif()
        if not exif:
            return None
        gps = exif.get_ifd(_GPS_IFD_TAG)
        if not gps or 1 not in gps or 2 not in gps or 3 not in gps or 4 not in gps:
            return None
        lat = _dms_to_deg(gps[2], gps[1])
        lng = _dms_to_deg(gps[4], gps[3])
        return (lat, lng)
    except Exception:
        return None


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    # NYC DCP GeoSearch (Pelias). NYC-only by design, no API key, no Nominatim
    # IP blocks. Returns the top-ranked match.
    query = urlencode({"text": address, "size": 1})
    req = Request(f"{_GEOSEARCH_URL}?{query}", headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except Exception:
        return None
    features = data.get("features") or []
    if not features:
        return None
    coords = features[0].get("geometry", {}).get("coordinates")
    if not coords or len(coords) < 2:
        return None
    lng, lat = coords[0], coords[1]
    return (float(lat), float(lng))


def _dms_to_deg(dms, ref: str) -> float:
    degrees = float(dms[0]) + float(dms[1]) / 60.0 + float(dms[2]) / 3600.0
    if ref in ("S", "W"):
        degrees = -degrees
    return degrees
