import json
import uuid
from pathlib import Path
from typing import Dict, List

_DATA_DIR = Path(__file__).parent / "data"
_GROUPS_FILE = _DATA_DIR / "groups.json"


def load_groups() -> List[Dict]:
    if not _GROUPS_FILE.exists():
        return []
    try:
        return json.loads(_GROUPS_FILE.read_text())
    except json.JSONDecodeError:
        return []


def save_group(title: str, neighborhood: str, meetup_time: str, creator: str) -> Dict:
    groups = load_groups()
    group = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "neighborhood": neighborhood,
        "meetup_time": meetup_time,
        "creator": creator,
        "members": [creator],
    }
    groups.append(group)
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _GROUPS_FILE.write_text(json.dumps(groups, indent=2))
    return group


def join_group(group_id: str, display_name: str) -> None:
    groups = load_groups()
    for g in groups:
        if g["id"] == group_id and display_name not in g["members"]:
            g["members"].append(display_name)
    _GROUPS_FILE.write_text(json.dumps(groups, indent=2))
