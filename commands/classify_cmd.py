from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import json
from typing import List


@dataclass
class _Row:
    filepath: str
    category: str
    confidence: float
    reason: str
    suggested_tags_json: str
    error: str | None


def run(path: Path, out: Path, model: str, dry_run: bool, max_chars: int, include_subdirs: bool, include_hidden: bool, fmt: str = "csv") -> int:
    # Local imports to avoid static analyzer issues
    from llm import make_client
    from file_reader import preview_file
    from io_utils import append_run_log
    from schemas import ClassificationResult
    from prompts import build_classify_prompt

    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw_responses"
    raw_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(path)
    files = list(input_path.iterdir()) if not include_subdirs else list(input_path.rglob("*"))
    files = [f for f in files if f.is_file()]

    results: List[_Row] = []
    client = make_client(model, dry_run=dry_run)

    total_tokens = 0
    total_cost = 0.0

    for f in files:
        try:
            preview = preview_file(f, max_chars=max_chars)
            prompt = build_classify_prompt(str(f), preview.text)
            # estimate
            tkns, cost = client.estimate_tokens_and_cost(prompt) if hasattr(client, 'estimate_tokens_and_cost') else (0, 0.0)
            total_tokens += tkns
            total_cost += cost

            # First attempt: raw send
            resp_text = client.send(prompt)
            parsed = None
            try:
                parsed = ClassificationResult.parse_raw(resp_text) if hasattr(ClassificationResult, 'parse_raw') else ClassificationResult(**json.loads(resp_text))
            except Exception:
                # Save raw response for auditing
                raw_file = raw_dir / (f.name + ".raw.txt")
                try:
                    raw_file.write_text(resp_text, encoding='utf-8')
                except Exception:
                    pass
                # Try repair via send_json (client handles repair prompting)
                try:
                    repaired = client.send_json(prompt)
                    parsed = ClassificationResult.parse_raw(repaired) if hasattr(ClassificationResult, 'parse_raw') else ClassificationResult(**json.loads(repaired))
                except Exception as e:
                    raise RuntimeError(f"LLM parsing failed; raw_saved={raw_file}; error={e}")

            row = _Row(
                filepath=str(f),
                category=parsed.category,
                confidence=parsed.confidence,
                reason=parsed.reason,
                suggested_tags_json=json.dumps(parsed.suggested_tags),
                error=None,
            )
        except Exception as e:
            row = _Row(filepath=str(f), category="", confidence=0.0, reason="", suggested_tags_json="[]", error=str(e))
        results.append(row)

    report_path = out / ("classification_report.csv" if fmt == "csv" else "classification_report.json")
    if fmt == "csv":
        with open(report_path, "w", newline='', encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["filepath", "category", "confidence", "reason", "suggested_tags_json", "error"])
            for r in results:
                writer.writerow([r.filepath, r.category, r.confidence, r.reason, r.suggested_tags_json, r.error or ""])
    else:
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump([asdict(r) for r in results], fh, ensure_ascii=False, indent=2)

    append_run_log(out, {
        "command": "classify",
        "model": model,
        "files_scanned": len(files),
        "files_processed": sum(1 for r in results if not r.error),
        "failures": sum(1 for r in results if r.error),
        "estimated_tokens": total_tokens,
        "estimated_cost": round(total_cost, 6),
    })

    return 0
