from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def append_run_log(out: Path, info: dict) -> None:
    logp = out / "run_log.json"
    record = {"timestamp": datetime.utcnow().isoformat() + "Z", **info}
    try:
        if logp.exists():
            with open(logp, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = []
    except Exception:
        data = []
    data.append(record)
    with open(logp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

