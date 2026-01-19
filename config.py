from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    openai_api_key: str | None = None

    @staticmethod
    def from_env() -> "Config":
        # Load .env if present in project root
        env_path = Path(__file__).resolve().parents[0] / '.env'
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and v and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                # ignore .env parsing errors
                pass
        return Config(openai_api_key=os.environ.get("OPENAI_API_KEY"))
