# Recipe Saver

Save recipes from a **website link**, a **YouTube video** or a **photo of a cookbook page**.
AI extracts the recipe, and you browse, search, edit and delete it in a React app. Recipes can be
organised into folders (a recipe can be in several), including by dragging a recipe onto a folder.
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

- **Backend:** Flask, SQLAlchemy, PostgreSQL, Pydantic, pytest (195 tests, 96% coverage), Alembic migrations
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

To measure the photo-correction guardrail against real AI output (needs your keys, costs a few cents):

```bash
cd backend && PYTHONPATH=. .venv/bin/python evals/corrector_eval.py
```
When a photo goes wrong in real use, add that recipe to `backend/evals/corrector_cases.py` so it stays fixed.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/recipes` | List recipes (oldest first) |
| GET | `/recipes/<id>` | Get one recipe |
| POST | `/recipes` | Create a recipe manually |
| PUT / PATCH | `/recipes/<id>` | Update a recipe |
| DELETE | `/recipes/<id>` | Delete a recipe |
| POST | `/recipes/extract` | Extract from `{"url": "..."}` (website or YouTube). Also saves the page's main image or the video thumbnail as the dish photo |
| POST | `/recipes/upload` | Extract from a photo (multipart field `image`) |
| POST | `/recipes/<id>/image` | Add or replace the dish photo (multipart field `image`) |
| DELETE | `/recipes/<id>/image` | Remove the dish photo |
| GET | `/images/<file>` | Serve a stored photo |
| GET / POST | `/folders` | List folders with recipe counts / create a folder |
| PATCH / DELETE | `/folders/<id>` | Rename a folder / delete it (its recipes are kept) |
| PUT / DELETE | `/folders/<id>/recipes/<recipe_id>` | Add a recipe to a folder (idempotent) / remove it from the folder |
| GET | `/health` | Health check |

A Postman collection with every endpoint is in `backend/Recipe_Saver.postman_collection.json`.

## Design decisions

- **Dish photos come from page metadata, not from AI.** Recipe sites and YouTube already say which picture
  represents the page (JSON-LD `image`, `og:image`, the video thumbnail). Reading that is free and instant
  and can't invent a URL. Photos are downloaded, re-encoded as resized JPEGs and stored on disk
  (`backend/uploads/`); the database keeps only the file name. Downloads refuse non-public addresses
  (SSRF protection) and a missing photo never blocks saving the recipe.
- **Folders are many-to-many.** A `recipe_folders` link table (composite primary key, `ON DELETE CASCADE`)
  lets one recipe live in several folders, and deleting a folder only removes the links, never the recipes.
  Adding a recipe is an idempotent `PUT`. The recipe list loads all links in one extra query
  (`selectinload`) to avoid the N+1 problem. In the UI a folder is a tile you can drag recipe cards onto.
- **Schema changes go through Alembic** (`backend/migrations/`). The migrations are idempotent, so the same
  `upgrade` works on a brand-new database and on one created earlier by `db.create_all()`.
- **Two AI providers, each for what it does best.** Gemini reads the image and OpenAI edits text.
  Thinking is set to LOW for OCR, which cut photo extraction from about 29 s to about 12 s.
- **The corrector is a proofreader, and its output is checked in code.** The model may only fix words the
  OCR misread and returns just the lines it changed, each quoting the original line. A deterministic
  gate (`review_correction`) then rejects any change that adds, removes or rewrites words, touches a
  number or a section header, or points at the wrong line. Step numbering is fixed in code, not by the AI.
- **The guardrail is measured, not guessed.** `backend/evals/` holds Hebrew recipes with known typos and
  correct recipes that must stay untouched. On that set, `gpt-4o-mini` with the old prompt missed typos and
  rewrote titles, and `gpt-4o` with the old prompt invented quantities. The current setup (`gpt-4o` plus the
  gate) fixed 21/21 typos with no wrong or false edits.
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
