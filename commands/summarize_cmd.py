from __future__ import annotations
from pathlib import Path
import json
import csv


def run(path: Path, out: Path, model: str, dry_run: bool, max_chars: int, include_subdirs: bool, include_hidden: bool) -> int:
    # Local imports
    from llm import make_client
    from file_reader import preview_file
    from io_utils import append_run_log
    from prompts import build_summarize_prompt

    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw_responses"
    raw_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(path)
    files = list(input_path.iterdir()) if not include_subdirs else list(input_path.rglob("*"))
    files = [f for f in files if f.is_file()]

    client = make_client(model, dry_run=dry_run)

    summaries_dir = out / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    index_rows = []
    folder_bullets = []

    total_tokens = 0
    total_cost = 0.0

    for f in files:
        try:
            preview = preview_file(f, max_chars=max_chars)
            prompt = build_summarize_prompt(str(f), preview.text)
            tkns, cost = client.estimate_tokens_and_cost(prompt) if hasattr(client, 'estimate_tokens_and_cost') else (0, 0.0)
            total_tokens += tkns
            total_cost += cost

            # First attempt raw
            resp_text = client.send(prompt)
            try:
                parsed = json.loads(resp_text)
            except Exception:
                raw_file = raw_dir / (f.name + ".raw.txt")
                try:
                    raw_file.write_text(resp_text, encoding='utf-8')
                except Exception:
                    pass
                try:
                    repaired = client.send_json(prompt)
                    parsed = json.loads(repaired)
                except Exception as e:
                    raise RuntimeError(f"LLM parsing failed; raw_saved={raw_file}; error={e}")

            summary = parsed.get("summary", "")
            short = (summary[:200] + "...") if len(summary) > 200 else summary

            outp = summaries_dir / (f.name + ".summary.txt")
            with open(outp, "w", encoding="utf-8") as fh:
                fh.write(summary)

            index_rows.append({"file": str(f), "summary_path": str(outp), "short_summary": short, "error": ""})
            folder_bullets.append({"filepath": str(f), "note": short})
        except Exception as e:
            index_rows.append({"file": str(f), "summary_path": "", "short_summary": "", "error": str(e)})

    index_path = out / "summaries_index.csv"
    with open(index_path, "w", newline='', encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["file", "summary_path", "short_summary", "error"])
        for r in index_rows:
            writer.writerow([r["file"], r["summary_path"], r["short_summary"], r["error"]])

    folder_summary = {
        "executive_summary": "",
        "themes": [],
        "notable_files": folder_bullets,
        "suggested_next_actions": [],
        "limitations": "Limitations: previews used, LLM summaries may be imperfect."
    }

    with open(out / "folder_summary.json", "w", encoding="utf-8") as fh:
        json.dump(folder_summary, fh, ensure_ascii=False, indent=2)

    append_run_log(out, {
        "command": "summarize",
        "model": model,
        "files_scanned": len(files),
        "files_processed": sum(1 for r in index_rows if not r["error"]),
        "failures": sum(1 for r in index_rows if r["error"]),
        "estimated_tokens": total_tokens,
        "estimated_cost": round(total_cost, 6),
    })

    return 0

