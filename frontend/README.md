# Recipe Saver — Frontend

React + TypeScript single-page app for saving recipes from websites, YouTube videos and photos.
It talks to the Flask API in `../backend`.

## Run it

```bash
# 1. Database and backend (from the repo root)
docker compose up -d
cd backend && python main.py          # API on http://127.0.0.1:5001

# 2. Frontend (in another terminal)
cd frontend
npm install                           # first time only
npm run dev                           # app on http://127.0.0.1:5173
```

Other scripts: `npm run build` (type-check + production build), `npm run lint` (oxlint).

## Stack

| Tool | Role |
|---|---|
| [Vite](https://vite.dev) | Dev server with instant reload, production bundler, and the `/api` proxy |
| React 19 + TypeScript | UI and type safety |
| [Tailwind CSS v4](https://tailwindcss.com) | Styling; design tokens live in `src/index.css` (`@theme`) |
| [React Router](https://reactrouter.com) | Client-side pages (`src/router.tsx`) |
| [TanStack Query](https://tanstack.com/query) | Server data: caching, loading/error state, refetching after changes |

## How it fits together

```
Browser ──> Vite :5173 ──/api/*──> Flask :5001 ──> PostgreSQL
              │  (proxy strips /api)
              └─ everything else: the React app
```

The browser only talks to Vite, so Flask needs no CORS setup. API calls use an `/api` prefix so they
never collide with page URLs: `/recipes/5` is the recipe *page*, `/api/recipes/5` is the *data*.

## Folder structure

```
src/
├── main.tsx            Entry point: sets up the query cache + router
├── router.tsx          URL -> page mapping
├── index.css           Tailwind import + theme (colors, font)
├── api/
│   ├── types.ts        Recipe type (mirrors the backend's Recipe.to_dict())
│   ├── client.ts       fetch wrapper: /api prefix, ApiError from {"error": ...} responses
│   └── recipes.ts      One function per endpoint + React Query hooks (useRecipes, useExtractFromUrl, …)
├── components/         Reusable pieces: Layout (header), RecipeCard, RecipeForm, RecipeMeta, StatusViews
├── pages/              One component per route: list, detail, add (link/photo/manual tabs), edit, 404
└── utils/
    └── textDirection.ts  Detects Hebrew/Arabic titles so the whole recipe renders right-to-left
```

## Design decisions worth knowing

- **Components never call `fetch` directly.** All server communication goes through `src/api`, so a
  backend change touches one folder.
- **Server state vs. UI state.** Data from the API lives in TanStack Query's cache; after a create/edit/delete
  the affected queries are invalidated so every screen shows fresh data. Local UI state (form fields,
  selected file) uses `useState`.
- **State in the URL where it helps.** The search text (`?q=`) and the active Add tab (`?tab=photo`) are
  URL parameters, so refresh, back button and shared links keep them.
- **Right-to-left support.** Recipes with a Hebrew title get `dir="rtl"` on their container, which mirrors
  the layout, not just the text. English UI badges inside them are pinned to `dir="ltr"` so
  "14 min cook" doesn't get reordered.
- **Slow AI requests feel responsive.** Extraction takes ~10–15s, so the UI shows a live timer and
  stage messages instead of a frozen button.
- **Validation in both places.** The form checks input instantly; the backend still validates because
  anyone can call the API directly.
