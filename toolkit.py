"""AI File & Document Automation Toolkit - CLI entrypoint

Usage (examples):
    python toolkit.py classify --path sample_folder --out output --model gpt-4o-mini
    python toolkit.py rename --path sample_folder --out output --model gpt-4o-mini
    python toolkit.py rename --path sample_folder --out output --apply
    python toolkit.py summarize --path sample_folder --out output --model gpt-4o-mini
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from commands import classify_cmd, rename_cmd, summarize_cmd
from config import Config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="toolkit.py", description="AI File & Document Automation Toolkit")
    sub = p.add_subparsers(dest="command", required=True)

    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument("--path", required=True, help="Path to folder to scan")
    common_args.add_argument("--out", default="output", help="Output directory")
    common_args.add_argument("--model", default="gpt-4o-mini", help="LLM model name")
    common_args.add_argument("--dry-run", action="store_true", help="Deterministic dry-run (no API calls)")
    common_args.add_argument("--max-chars", type=int, default=2000, help="Max characters to preview per file")
    common_args.add_argument("--include-subdirs", action="store_true")
    common_args.add_argument("--include-hidden", action="store_true")

    c1 = sub.add_parser("classify", parents=[common_args], help="Classify files and write a report")
    c1.add_argument("--format", choices=["csv", "json"], default="csv")

    c2 = sub.add_parser("rename", parents=[common_args], help="Suggest safe filenames; use --apply to execute")
    c2.add_argument("--apply", action="store_true", help="Apply proposed renames (destructive)")

    c3 = sub.add_parser("summarize", parents=[common_args], help="Summarize files and produce folder-level summary")

    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = Config.from_env()
    path = Path(args.path)
    out = Path(args.out)

    common = dict(
        path=path,
        out=out,
        model=args.model,
        dry_run=bool(args.dry_run),
        max_chars=int(args.max_chars),
        include_subdirs=bool(args.include_subdirs),
        include_hidden=bool(args.include_hidden),
    )

    if args.command == "classify":
        return classify_cmd.run(**common, fmt=args.format)
    if args.command == "rename":
        return rename_cmd.run(**common, apply=bool(args.apply))
    if args.command == "summarize":
        return summarize_cmd.run(**common)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

