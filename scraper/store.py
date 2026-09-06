from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class SeenStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._urls: set[str] = set(load_json(path, []))

    @property
    def urls(self) -> set[str]:
        return set(self._urls)

    def contains(self, url: str) -> bool:
        return url.rstrip("/") in self._urls or url in self._urls

    def add(self, url: str) -> None:
        self._urls.add(url.rstrip("/"))

    def persist(self) -> None:
        save_json(self.path, sorted(self._urls))
