import json


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
