from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Article:
    url: str
    title: str
    standfirst: str
    public_text: str
    image_url: str
    published_at: str
    tags: list[str] = field(default_factory=list)
    source_en: str = ""
    source_fa: str = ""
    tech_score: int = 0

    def to_dict(self) -> dict:
        return asdict(self)
