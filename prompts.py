from __future__ import annotations

def build_classify_prompt(filepath: str, preview_text: str) -> str:
    return (
        "You are a classification assistant. MUST RESPOND WITH VALID JSON ONLY. "
        "Do not add any explanation, markdown, or code fences — return EXACTLY one JSON object.\n"
        "Schema: {\n  \"category\": string,\n  \"confidence\": number (0.0-1.0),\n  \"reason\": string,\n  \"suggested_tags\": [string,...]\n}\n"
        "Example: {\"category\": \"notes\", \"confidence\": 0.85, \"reason\": \"Filename + preview indicate meeting notes\", \"suggested_tags\": [\"meeting\",\"notes\"] }\n\n"
        f"File: {filepath}\nPreview (truncated):\n{preview_text}\n\nReturn JSON only."
    )


def build_rename_prompt(filepath: str, preview_text: str) -> str:
    return (
        "You are a filename-suggestion assistant. MUST RESPOND WITH VALID JSON ONLY. "
        "Return EXACTLY one JSON object with keys: {\n  \"proposed_filename\": string,  // filename only, no path\n  \"reason\": string,\n  \"safe\": boolean\n}\n"
        "Rules:\n- Use kebab-case (lowercase, hyphens).\n- Preserve the original file extension (do NOT include extension in proposed_filename — tool will append it).\n- Do NOT include PII (emails, phone numbers) in the filename.\n- Do not include any explanation or extra text.\n"
        "Example: {\"proposed_filename\": \"meeting-notes-acme-corp-2024-11-01\", \"reason\": \"Content looks like meeting notes\", \"safe\": true }\n\n"
        f"File: {filepath}\nPreview (truncated):\n{preview_text}\n\nReturn JSON only."
    )


def build_summarize_prompt(filepath: str, preview_text: str) -> str:
    return (
        "You are a summarization assistant. MUST RESPOND WITH VALID JSON ONLY. "
        "Return EXACTLY one JSON object: {\n  \"summary\": string\n}\n"
        "Guidelines: produce a short (1-3 sentence) human-readable summary focusing on main points and notable metadata. Avoid adding suggestions.\n"
        "Example: {\"summary\": \"Meeting notes: discussed project timeline and task assignments for Acme Corp.\" }\n\n"
        f"File: {filepath}\nPreview (truncated):\n{preview_text}\n\nReturn JSON only."
    )
