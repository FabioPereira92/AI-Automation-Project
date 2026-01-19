from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import json
import shutil
import re


@dataclass
class _Row:
    filepath: str
    proposed_name: str
    proposed_path: str
    reason: str
    safe: bool
    collision: bool
    error: str | None


def run(path: Path, out: Path, model: str, dry_run: bool, max_chars: int, include_subdirs: bool, include_hidden: bool, apply: bool = False) -> int:
    # Local imports
    from llm import make_client
    from file_reader import preview_file
    from io_utils import append_run_log
    from planners import is_valid_filename
    from prompts import build_rename_prompt
    from schemas import RenameResult

    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw_responses"
    raw_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(path)
    files = list(input_path.iterdir()) if not include_subdirs else list(input_path.rglob("*"))
    files = [f for f in files if f.is_file()]

    client = make_client(model, dry_run=dry_run)

    rows: list[_Row] = []
    backup = {}

    total_tokens = 0
    total_cost = 0.0

    for f in files:
        try:
            preview = preview_file(f, max_chars=max_chars)
            prompt = build_rename_prompt(str(f), preview.text)
            tkns, cost = client.estimate_tokens_and_cost(prompt) if hasattr(client, 'estimate_tokens_and_cost') else (0, 0.0)
            total_tokens += tkns
            total_cost += cost

            # Raw
            resp_text = client.send(prompt)
            try:
                parsed = RenameResult.parse_raw(resp_text) if hasattr(RenameResult, 'parse_raw') else RenameResult(**json.loads(resp_text))
            except Exception:
                raw_file = raw_dir / (f.name + ".raw.txt")
                try:
                    raw_file.write_text(resp_text, encoding='utf-8')
                except Exception:
                    pass
                try:
                    repaired = client.send_json(prompt)
                    parsed = RenameResult.parse_raw(repaired) if hasattr(RenameResult, 'parse_raw') else RenameResult(**json.loads(repaired))
                except Exception as e:
                    raise RuntimeError(f"LLM parsing failed; raw_saved={raw_file}; error={e}")

            prop_name = parsed.proposed_filename
            safe = parsed.safe
            reason = parsed.reason

            # Ensure extension preserved
            ext = f.suffix
            if not prop_name.endswith(ext):
                prop_name = prop_name + ext

            # sanitize
            prop_name = re.sub(r"[\\/:*?\"<>|]", "-", prop_name)

            proposed_path = str(Path(f.parent) / prop_name)
            collision = Path(proposed_path).exists()

            row = _Row(filepath=str(f), proposed_name=prop_name, proposed_path=proposed_path, reason=reason, safe=safe, collision=collision, error=None)

            if apply and safe and not collision and not dry_run:
                newp = Path(proposed_path)
                shutil.move(str(f), str(newp))
                backup[str(f)] = str(newp)

        except Exception as e:
            row = _Row(filepath=str(f), proposed_name="", proposed_path="", reason="", safe=False, collision=False, error=str(e))
        rows.append(row)

    plan_path = out / "rename_plan.csv"
    with open(plan_path, "w", newline='', encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["filepath", "proposed_name", "proposed_path", "reason", "safe", "collision", "error"])
        for r in rows:
            writer.writerow([r.filepath, r.proposed_name, r.proposed_path, r.reason, str(r.safe), str(r.collision), r.error or ""])

    backup_path = out / "rename_backup.json"
    with open(backup_path, "w", encoding="utf-8") as fh:
        json.dump(backup, fh, ensure_ascii=False, indent=2)

    append_run_log(out, {
        "command": "rename",
        "model": model,
        "files_scanned": len(files),
        "files_processed": sum(1 for r in rows if not r.error),
        "failures": sum(1 for r in rows if r.error),
        "applied": apply,
        "estimated_tokens": total_tokens,
        "estimated_cost": round(total_cost, 6),
    })

    return 0
