import json

DEFAULT_PATH = "user_history.json"

def load_user_history(path: str = DEFAULT_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_history(data: dict, path: str = DEFAULT_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)