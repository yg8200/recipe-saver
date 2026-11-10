# Recipe Saver

Save recipes from a **website link**, a **YouTube video** or a **photo of a cookbook page**.
AI extracts the recipe, and you browse, search, edit and delete it in a React app.
The interface is in Hebrew with a full right-to-left layout (English recipes still display correctly).

<!-- Add a screenshot or GIF here: ![Recipe Saver](docs/screenshot.png) -->

## How it works

| Source | Pipeline |
|---|---|
| **Website** | Scraped with `curl_cffi` (Chrome TLS fingerprint) and `BeautifulSoup`, then OpenAI extracts it into a Pydantic schema. |
| **YouTube** | The video description is tried first. The transcript is used only to fill in what is missing (e.g. ingredients without steps). |
| **Photo** (JPEG, PNG, HEIC) | The image is resized, Gemini reads the text, then OpenAI fixes OCR typos and returns only the lines it changed. |

Every extraction passes a deterministic validator before it reaches the database.

## Tech stack

- **Backend:** Flask, SQLAlchemy, PostgreSQL, Pydantic, pytest (106 tests, 92% coverage)
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, React Router, TanStack Query
- **AI:** OpenAI (extraction and correction), Google Gemini (photo OCR)
- **Infra:** Docker Compose (Postgres, backend, nginx-served frontend, pgAdmin)

## Run with Docker

You need Docker and your own API keys.

```bash
cp backend/.env.example backend/.env    # then add OPENAI_API_KEY and GEMINI_API_KEY
docker compose up -d --build
```

- App: <http://localhost:8080>
- API: <http://localhost:5001>
- pgAdmin: <http://localhost:5050>

The passwords in `docker-compose.yml` (`postgres`, `admin`) are local development defaults only.

## Run for development

```bash
docker compose up -d db                              # just the database

cd backend
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python main.py                             # http://localhost:5001

cd frontend
npm install && npm run dev                           # http://localhost:5173 (proxies /api to Flask)
```

## Tests

```bash
cd backend && .venv/bin/python -m pytest --cov=src --cov-report=term-missing
cd frontend && npm run build && npm run lint
```

All AI calls are mocked in tests, so they need no API keys and cost nothing.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/recipes` | List recipes (oldest first) |
| GET | `/recipes/<id>` | Get one recipe |
| POST | `/recipes` | Create a recipe manually |
| PUT / PATCH | `/recipes/<id>` | Update a recipe |
| DELETE | `/recipes/<id>` | Delete a recipe |
| POST | `/recipes/extract` | Extract from `{"url": "..."}` (website or YouTube) |
| POST | `/recipes/upload` | Extract from a photo (multipart field `image`) |
| GET | `/health` | Health check |

A Postman collection with every endpoint is in `backend/Recipe_Saver.postman_collection.json`.

## Design decisions

- **Two AI providers, each for what it does best.** Gemini reads the image and OpenAI edits text.
  Thinking is set to LOW for OCR, which cut photo extraction from about 29 s to about 12 s.
- **The corrector returns only changed lines.** This saves output tokens, and a bad answer can never
  delete or reorder content. Step numbering is fixed in code, not by the AI.
- **AI output is never trusted.** A deterministic validator checks every extraction before saving,
  and the photo route falls back to the raw OCR text if the corrector fails.
- **One origin for the browser.** Vite in development and nginx in Docker both proxy `/api` to Flask,
  so the backend needs no CORS configuration.

## Known limitations and next steps

- Duplicates are detected by title, so re-extracting the same link can save a copy. The plan is to store
  `source_url`, which needs database migrations (Alembic).
- No authentication yet, and the Flask dev server is used. A production setup would add auth and gunicorn.
- Slow AI calls run inside the request. Background jobs would improve this.

## License

[MIT](LICENSE)
