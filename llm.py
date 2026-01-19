from __future__ import annotations
import json
import hashlib
import os
import time
from typing import Optional, Tuple

import requests


class LLMClient:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def send(self, prompt: str) -> str:
        raise NotImplementedError

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        # Remove common Markdown code fences like ```json ... ``` or ``` ... ```
        if not text:
            return text
        txt = text.strip()
        # If fenced block present, extract inner content
        if txt.startswith("```") and txt.endswith("```"):
            # remove the starting ```[lang]? and ending ```
            # find first newline after opening fence
            first_nl = txt.find('\n')
            if first_nl != -1:
                inner = txt[first_nl+1:-3]
                return inner.strip()
            else:
                return txt.strip('`')
        # Otherwise remove inline fences if present
        # replace any occurrence of ```json or ``` with empty markers
        txt = txt.replace('```json', '')
        txt = txt.replace('```', '')
        return txt.strip()

    @staticmethod
    def try_extract_json(text: str) -> Optional[str]:
        # Normalize and strip code fences
        if not text:
            return None
        cleaned = LLMClient._strip_code_fences(text)
        if '{' not in cleaned:
            return None
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = cleaned[start:end+1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            return None

    def send_json(self, prompt: str, *, retry: bool = True) -> str:
        """Send prompt and enforce JSON output. First try direct call and automatic extraction; if parsing fails and retry is True, send a repair prompt once including the previous response for context."""
        resp = self.send(prompt)
        # First, direct parse
        try:
            json.loads(resp)
            return resp
        except Exception:
            # Try auto extraction heuristics
            extracted = self.try_extract_json(resp)
            if extracted:
                return extracted
            if not retry:
                raise
            # Repair: include the previous response to help the model
            repair_prompt = (
                "Previous response was not valid JSON. Here is the previous response:\n``\n"
                + (resp[:5000] if len(resp) > 5000 else resp)
                + "\n```\nPlease re-output the result as VALID JSON only for the original request: \n"
                + prompt
            )
            resp2 = self.send(repair_prompt)
            # Try extraction again
            try:
                json.loads(resp2)
                return resp2
            except Exception:
                extracted2 = self.try_extract_json(resp2)
                if extracted2:
                    return extracted2
                raise ValueError("LLM did not return valid JSON after repair attempt")

    def estimate_tokens_and_cost(self, prompt: str) -> Tuple[int, float]:
        # Very rough token estimate: 4 chars per token
        chars = len(prompt)
        tokens = max(1, int(chars / 4))
        # rough cost per 1k tokens (USD) - conservative estimate; adjust per model
        cost_per_1k = 0.03
        cost = tokens / 1000.0 * cost_per_1k
        return tokens, cost


class OpenAIClient(LLMClient):
    def __init__(self, model_name: str, api_key: Optional[str] = None, timeout: int = 30):
        super().__init__(model_name)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment; cannot initialize OpenAIClient")
        self.timeout = timeout
        self.endpoint = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1/responses")

    def send(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model_name, "input": prompt}
        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            j = resp.json()
            # Try common Responses API shapes
            # 1) j["output"][0]["content"][0]["text"]
            content = None
            try:
                content = j.get("output", [])[0].get("content", [])[0].get("text")
            except Exception:
                content = None
            if not content:
                # 2) some SDKs return output_text
                content = j.get("output_text") or j.get("text")
            if not content:
                # 3) fallback: concatenate any strings in output
                out = j.get("output")
                if isinstance(out, list):
                    parts = []
                    for item in out:
                        if isinstance(item, dict):
                            for c in item.get("content", []):
                                if isinstance(c, dict) and "text" in c:
                                    parts.append(c.get("text"))
                        elif isinstance(item, str):
                            parts.append(item)
                    content = "\n".join(p for p in parts if p)
            if content is None:
                # As last resort, try to extract JSON object from raw text
                text = resp.text
                extracted = self.try_extract_json(text)
                if extracted:
                    return extracted
                return text
            return content
        except requests.RequestException as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")


class MockLLMClient(LLMClient):
    def __init__(self, model_name: str = "mock"):
        self.model_name = model_name

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def send(self, prompt: str) -> str:
        # Deterministic fake outputs derived from prompt hash
        h = self._hash(prompt)
        lp = prompt.lower()
        # Recognize classify prompts
        if "classify file" in lp or "respond in strict json with keys: category" in lp:
            out = {
                "category": "notes",
                "confidence": 0.85,
                "reason": "Filename and content look like meeting notes",
                "suggested_tags": ["meeting", "notes"]
            }
            return json.dumps(out)

        # Recognize rename prompts
        if "suggest a safe filename" in lp or "suggest filename" in lp or "proposed_filename" in lp or "suggested filename" in lp:
            base = f"file-{h[:8]}"
            out = {
                "proposed_filename": base,
                "reason": "Generated deterministically from preview and filepath",
                "safe": True
            }
            return json.dumps(out)

        # Recognize repair requests
        if "previous response" in lp or "invalid json" in lp or "please output strict json" in lp or "repair" in lp:
            if "category" in lp:
                out = {
                    "category": "notes",
                    "confidence": 0.75,
                    "reason": "Repair: guessed category",
                    "suggested_tags": ["notes"]
                }
                return json.dumps(out)
            if "proposed_filename" in lp or "filename" in lp:
                base = f"file-{h[:8]}"
                out = {
                    "proposed_filename": base,
                    "reason": "Repair: generated filename",
                    "safe": True
                }
                return json.dumps(out)
            return json.dumps({"summary": f"Summary based on hash {h[:10]}"})

        # Default to summary
        out = {"summary": f"Summary based on hash {h[:10]}"}
        return json.dumps(out)


# Helper factory
def make_client(model_name: str, dry_run: bool = False) -> LLMClient:
    if dry_run:
        return MockLLMClient(model_name=model_name)
    # If OPENAI_API_KEY not set, fall back to mock but warn
    if not os.environ.get("OPENAI_API_KEY"):
        return MockLLMClient(model_name=model_name)
    return OpenAIClient(model_name=model_name)
