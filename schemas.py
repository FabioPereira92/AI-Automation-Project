from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import re


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reason: str
    suggested_tags: List[str] = field(default_factory=list)

    @staticmethod
    def parse_raw(text: str) -> "ClassificationResult":
        import json
        d = json.loads(text)
        return ClassificationResult(category=d.get("category", ""), confidence=float(d.get("confidence", 0.0)), reason=d.get("reason", ""), suggested_tags=d.get("suggested_tags", []))


@dataclass
class RenameResult:
    proposed_filename: str
    reason: str
    safe: bool

    @staticmethod
    def parse_raw(text: str) -> "RenameResult":
        import json
        d = json.loads(text)
        return RenameResult(proposed_filename=d.get("proposed_filename", ""), reason=d.get("reason", ""), safe=bool(d.get("safe", False)))


@dataclass
class FolderSummary:
    executive_summary: str
    themes: List[str]
    notable_files: List[dict]
    suggested_next_actions: List[str]
    limitations: str

