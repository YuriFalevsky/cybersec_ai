# 🔍 Vuln-Scan-MCP

**Vuln-Scan-MCP** — это асинхронный сканер веб-уязвимостей, который:

* генерирует payload-ы через **локальную LLM** (φ-, Llama-, Mistral-совместимые REST-эндпоинты);
* использует **Model-Context-Protocol (MCP)**, чтобы LLM-агенты могли вызывать инструменты (`scan_url`, `generate_payloads`, `lookup_attack_db`, `reconnaissance`) без «обвязки»;
* обучается на собственных результатах (RAG + CatBoost ранжировщик);
* имеет встроенную «базу атак» — быстрая отдача готовых эксплойтов из PayloadsAllTheThings, Exploit-DB и т. д.;
* показывает прогресс в real-time через WebSocket и сохраняет историю в SQLite/PostgreSQL.

---

## 📁 Структура проекта

app/
├── main.py ⇠ FastAPI UI + REST + WS
├── db.py ⇠ SQLAlchemy (SQLite / Postgres)
├── utils.py ⇠ inject(), body_hash() …
├── services/
│ ├── http.py ⇠ async_scan()
│ ├── llm.py ⇠ gen_payloads_with_memory()
│ ├── recon.py ⇠ whatweb / nuclei wrapper
│ └── attack_db.py ⇠ локальная база пейлоадов
├── workflows/
│ └── precise_scan.py ⇠ baseline → payload-loop
└── templates/index.html ⇠ минимальный UI
data/attacks.json ⇠ «PayloadsAllTheThings» выжимка
mcp_server.py ⇠ MCP-инструменты
Dockerfile
docker-compose.yml

yaml
Копировать
Редактировать

---

## 🚀 Быстрый старт

### 1. С Docker (рекомендуется)

```bash
git clone https://github.com/your-org/vuln-scan-mcp.git
cd vuln-scan-mcp

# укажите адрес и модель вашей локальной LLM
export LLM_API_URL="http://10.147.20.151:8000/generate"
export LLM_MODEL="phi3:mini-128k-instruct"

docker compose up --build
Сервис	Порт	Что внутри
api	8000	UI + REST + WS
mcp	3333	MCP-tools
db	5432	(опц.) Postgres

Откройте http://localhost:8000 и запустите скан первой цели.

2. Локально (два терминала)
bash
Копировать
Редактировать
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export LLM_API_URL="http://10.147.20.151:8000/generate"
export LLM_MODEL="phi3:mini-128k-instruct"

# терминал 1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# терминал 2
python mcp_server.py --port 3333
⚙️ Переменные окружения
Переменная	Дефолт	Описание
LLM_API_URL	http://10.147.20.151:8000/generate	REST-эндпоинт локальной LLM
LLM_MODEL	phi3:mini-128k-instruct	имя модели, передаваемое в payload
DB_URL	sqlite+aiosqlite:///./scanner.db	строка SQLAlchemy (смените на Postgres)
LLM_TIMEOUT	60	таймаут HTTP-запроса к LLM (сек)

🛠️ Инструменты MCP
Имя	Аргументы	Что делает
scan_url	url, method, headers, params, data	Асинхронный HTTP-запрос, метрики + хэш
generate_payloads	vuln_type, baseline, n	Генерация N payload-ов через LLM
lookup_attack_db	vuln_type, url, limit	Быстрый поиск готовых эксплойтов
reconnaissance	url	WhatWeb + nuclei отчёт (JSON-путь)

Любой LLM-агент с поддержкой MCP (Claude Desktop, Autogen, OpenDevin и т. д.) может вызывать эти функции напрямую.

🏃 API & UI
HTTP метод	Эндпоинт	Описание
POST	/scan_precise	url, vuln_type → асинхронная сессия; ответ {"session_id":…}
WS	/ws/{session_id}	Stream JSON-ивентов (baseline, probe, finished)
POST	/recon	полная рекогносцировка цели

📊 Как это работает
Baseline-запрос → сохраняем метрики.

LLM получает:

top-N готовых payload-ов из data/attacks.json;

few-shot из похожих прошлых сканов (vector search + pgvector);

системную инструкцию «верни JSONpayloads».

Возврат > ранжирование CatBoost → стрельба топ-5.

Diff-логика определяет успех, результаты пишутся в payload_history.

MCP-агенты могут вмешиваться в любой шаг, переиспользуя инструменты.

🧩 Расширение
Добавьте словарь в data/attacks.json — мгновенно доступен в lookup_attack_db.

Подключите Zap/ffuf/Nuclei — допишите async wrapper внутри services/recon.py.

Веб-фронт — замените templates/index.html на React SPA и используйте тот же WS-эндпоинт.

CatBoost retrain — смотрите scripts/retrain_ranker.py.

👥 Contributing
fork → git clone → создайте ветку.

Проверка кода: ruff check . && mypy app

Тесты: pytest -q

PR + описание/скриншот работы UI.

📜 License
MIT. See LICENSE.

💬 Контакты
Issues — GitHub Issues.

TG-чат — @vulnscan_mcp.

Авторы — team-mcp.
