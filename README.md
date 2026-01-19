# AI File & Document Automation Toolkit 📁🤖

AI File & Document Automation Toolkit is a CLI utility to safely scan folders and perform AI-assisted classification, renaming suggestions, and summaries for text-like files. It's designed for productivity workflows and keeps a human-in-the-loop model: destructive actions are never taken without an explicit `--apply` flag.

Who it's for
- Freelancers, knowledge workers, and teams who want to tidy file systems, index documents, and get quick summaries. 💼✨

Before / After example
- Before: folder with 100 ambiguous notes files like `note1.txt`, `doc2.txt`. 🗂️
- After: `output/rename_plan.csv` with safe proposed names, `output/summaries/` with short human-reviewable summaries. ✅

Usage examples

Dry-run classify:

```bash
python toolkit.py classify --path sample_folder --out output --model gpt-4o-mini --dry-run
```

Rename (plan):

```bash
python toolkit.py rename --path sample_folder --out output --model gpt-4o-mini
```

Rename (apply):

```bash
python toolkit.py rename --path sample_folder --out output --model gpt-4o-mini --apply
```

Summarize:

```bash
python toolkit.py summarize --path sample_folder --out output --model gpt-4o-mini
```

Safety model 🔒
- Default dry-run: no API calls unless `--dry-run` is false and API key configured. ⚠️
- Previews only: files are never uploaded fully by default; only a limited preview (`--max-chars`) is sent to the model. 📏
- Human review required: `rename` never renames unless `--apply` is passed. 🙋‍♂️

AI disclosure 🧾
- Developed using GitHub Copilot and ChatGPT as productivity tools. All design decisions validated by author.

Limits & notes ⚙️
- Python 3.11 recommended.
- The project includes `MockLLMClient` for deterministic testing and dry-run behaviour. 🧪

Placeholders 📸
- Add screenshot/GIF here

Contributing 🤝
- PRs welcome. Please run `pytest` and ensure linting.
