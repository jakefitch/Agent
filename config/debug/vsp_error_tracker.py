import json
from pathlib import Path
from datetime import datetime

ERROR_LOG_PATH = Path("config/debug/vsp_errors.json")


def save_vsp_error_message(message: str) -> None:
    """Save a VSP error banner message to a JSON file with timestamp."""
    error_record = {
        "timestamp": datetime.now().isoformat(),
        "message": message.strip(),
    }

    existing = []
    if ERROR_LOG_PATH.exists():
        try:
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []

    if any(e.get("message") == error_record["message"] for e in existing):
        return

    existing.append(error_record)
    with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def load_vsp_errors():
    """Load previously stored VSP error messages."""
    if ERROR_LOG_PATH.exists():
        try:
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []
