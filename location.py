from io import BytesIO

from PIL import Image
from geopy.geocoders import Nominatim

_GPS_IFD_TAG = 0x8825
_geocoder = Nominatim(user_agent="trashai-cuny-aic-2026")


def get_location_from_exif(image_bytes: bytes) -> tuple[float, float] | None:
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


def geocode_address(address: str) -> tuple[float, float] | None:
    try:
        location = _geocoder.geocode(address, timeout=10)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception:
        return None


def _dms_to_deg(dms, ref: str) -> float:
    degrees = float(dms[0]) + float(dms[1]) / 60.0 + float(dms[2]) / 3600.0
    if ref in ("S", "W"):
        degrees = -degrees
    return degrees
