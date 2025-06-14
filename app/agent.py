from __future__ import annotations
import json, textwrap
from typing import Optional

from .url_loader import fetch
from .llm_http import HTTPLLMClient

PROMPT_TEMPLATE = """
{user_prompt}

----- TARGET RESPONSE -----
Status code : {status_code}
Length      : {length}
Latency     : {latency:.2f}s

Body (truncated):
{body}

### Ответ:
"""

class URLAnalysisAgent:
    def __init__(self, llm_client: Optional[HTTPLLMClient] = None):
        self.llm = llm_client or HTTPLLMClient()

    def analyze(self, user_prompt: str, url: str) -> str | dict:
        resp = fetch(url)
        prompt = PROMPT_TEMPLATE.format(
            user_prompt=textwrap.dedent(user_prompt).strip(),
            **resp
        )
        raw = self.llm.generate(prompt)
        return raw
