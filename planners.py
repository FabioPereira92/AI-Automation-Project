from __future__ import annotations
import re
from pathlib import Path


def build_rename_plan(original_path: Path, proposed_name: str) -> dict:
    # Return a dict suitable for CSV writing
    return {
        "filepath": str(original_path),
        "proposed_name": proposed_name,
        "proposed_path": str(original_path.parent / proposed_name),
    }


def is_valid_filename(name: str) -> bool:
    # Basic cross-platform check
    if not name or len(name) > 255:
        return False
    if re.search(r"[\\/:*?\"<>|]", name):
        return False
    return True

