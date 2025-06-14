import os

# ──────────────── LLM ────────────────
LLM_API_URL = os.getenv("LLM_API_URL", "http://10.147.20.151:8000/generate")
LLM_MODEL   = os.getenv("LLM_MODEL",   "gemma3:4b-it-qat")
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "-1"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))  # секунд


# ──────────────── HTTP fetch ─────────
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10"))  # сек
MAX_BODY_CHARS  = int(os.getenv("MAX_BODY_CHARS", "15000"))  # обрезаем тело
