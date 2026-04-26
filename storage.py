import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).parent / "data"
_PINS_FILE = _DATA_DIR / "pins.json"
_IMAGES_DIR = _DATA_DIR / "images"


def load_pins() -> list[dict]:
    if not _PINS_FILE.exists():
        return []
    try:
        return json.loads(_PINS_FILE.read_text())
    except json.JSONDecodeError:
        return []


def save_pin(
    lat: float,
    lng: float,
    category: str,
    display_name: str,
    image_bytes: bytes,
    reasoning: str = "",
    notable_details: str = "",
    confidence: str = "",
) -> dict:
    _IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_name = f"{uuid.uuid4().hex}.jpg"
    (_IMAGES_DIR / image_name).write_bytes(image_bytes)

    pin = {
        "lat": lat,
        "lng": lng,
        "category": category,
        "display_name": display_name,
        "image": image_name,
        "reasoning": reasoning,
        "notable_details": notable_details,
        "confidence": confidence,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    pins = load_pins()
    pins.append(pin)
    _PINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PINS_FILE.write_text(json.dumps(pins, indent=2))
    return pin


def load_image(image_name: str) -> Optional[bytes]:
    path = _IMAGES_DIR / image_name
    if not path.exists():
        return None
    return path.read_bytes()
