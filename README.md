# BearingPulse — Amazon India price intelligence for bearing distributors

BearingPulse monitors Amazon India listings for a bearing catalogue (SKF by default). It discovers ASINs from search
results, refreshes product pages, sweeps competing seller offers across simulated PIN codes, stores every observation
as a time series, raises alerts on price drops / Buy Box changes / stock-outs, and presents it all in a React dashboard
backed by a FastAPI service.

> **Responsible use.** Automated access to Amazon may breach Amazon's Conditions of Use. Review the terms, keep request
> rates conservative, and use the tool only where you are permitted to. You are responsible for how you run it.

## Features

- **Dashboard (React)** — overview KPIs, product and seller tables with search + pagination, product detail with
  multi-seller price history (7/30/90 days), Buy Box share, alert inbox with acknowledge / bulk-acknowledge / CSV export,
  analytics (price leaders, undercut events), settings (persisted alert thresholds, on-demand crawl jobs, system status).
- **Landing page** with animated hero, scroll-triggered sections and a mascot; dark/light themes; fully responsive;
  honours `prefers-reduced-motion`.
- **REST API (FastAPI)** — API-key auth (constant-time compare), pagination (`X-Total-Count`), search, CRUD for tracked
  products, persisted alert configuration, CSV export, task-queue triggers, health endpoint.
- **Crawling** — Scrapy spiders (search, product detail, seller offers), Playwright fallback for JS-heavy pages, user-agent
  and proxy rotation (ScrapeOps or your own list), PIN-code simulation, blocked-response retry.
- **Scheduling** — Celery + Redis beat schedule (search every 6h, product refresh every 2h, alert check every 15 min).
  The seller-offer sweep is on-demand only: see Known limitations. Alerts can be emailed (SMTP) or posted to a webhook.
- **Legacy Streamlit dashboard** — retained under `dashboard/` (optional; see notes).

## Architecture

```text
 Scrapy spiders ──► Parser/Validator ──► PostgreSQL ◄── Alert engine ◄── Celery beat/worker ◄── Redis
   │  (UA + proxy rotation,                  ▲                                   ▲
   │   Playwright fallback)                  │                                   │
   └──────────────────────────────────────── FastAPI (/api) ─── trigger jobs ────┘
                                                ▲
                                     React SPA (Vite) / nginx
```

| Path | Purpose |
| --- | --- |
| `api/` | FastAPI app, routers (`asins`, `sellers`, `alerts`, `analytics`, `crawl`), auth, pagination |
| `db/` | SQLAlchemy models, async engine, CRUD/queries, Alembic migrations (`db/migrations`) |
| `scraper/`, `playwright_scraper/`, `anti_bot/` | Scrapy project, middlewares, headless fallback, proxy/UA/geo helpers |
| `data_pipeline/` | HTML parsers, normalisers, Pydantic validators, alert engine |
| `scheduler/` | Celery app, beat schedule, tasks |
| `frontend/` | React 18 + Vite SPA (router, hand-rolled SVG charts, no UI framework) |
| `dashboard/` | Legacy Streamlit UI |
| `scripts/seed_dev_data.py` | Optional synthetic data for **local development only** |
| `tests/` | Pytest suite (API, CRUD, parsers, validators, pipeline) |

## Prerequisites

- **Docker route:** Docker Desktop / Engine with Compose v2.
- **Local route:** Python 3.11+, Node.js 20+ (22 recommended). PostgreSQL 14+ and Redis 6+ are needed for the full
  stack; for just the API + UI you can use SQLite (see below).
- Optional: a [ScrapeOps](https://scrapeops.io) API key or your own proxy list for real crawling.

## Configuration

```bash
cp .env.example .env
```

Edit `.env` — every `replace-with-…` value must be set. Key variables:

| Variable | Description |
| --- | --- |
| `API_KEY` | Shared secret for the API / dashboard sign-in. In `APP_ENV=production` the server refuses to start with a default value. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Postgres container credentials (must match `DATABASE_URL`). |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/db` (or `sqlite:///./dev.db` for local dev). |
| `REDIS_URL` | Celery broker/result backend and health probe. |
| `CORS_ORIGINS` | Comma-separated browser origins allowed to call the API. |
| `SCRAPEOPS_API_KEY`, `PROXY_LIST` | Proxy providers (optional). |
| `ALERT_THRESHOLD_PCT`, `ALERT_EMAIL`, `ALERT_WEBHOOK_URL`, `SMTP_*` | Alert defaults and delivery. |
| `FLOWER_BASIC_AUTH` | `user:password` protecting the Flower UI. |

`.env` is git-ignored; never commit it. Alert thresholds saved in the UI are stored in the database and override
`ALERT_THRESHOLD_PCT`.

## Run with Docker (recommended)

```bash
cp .env.example .env     # then edit secrets
docker compose up --build -d
```

This starts Postgres, Redis, the API (migrations run automatically on boot), nginx serving the React app, a Celery worker,
Celery beat and Flower.

- App: <http://localhost:3000> — sign in with your `API_KEY`
- API health: <http://localhost:8000/api/health>
- Flower: <http://127.0.0.1:5555>
- Legacy Streamlit (optional): `docker compose --profile legacy up -d` → <http://localhost:8501>

Windows helper: `./start-all.ps1 -Detach` (checks `.env`, starts services, waits for the API).

## Run locally without Docker

### Backend

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium          # only needed for crawling
```

Minimal environment (SQLite, no Redis/Celery):

```bash
export DATABASE_URL=sqlite:///./dev.db API_KEY=dev-local-key APP_ENV=development   # PowerShell: $env:VAR="..."
alembic upgrade head                 # create / upgrade the schema
python -m scripts.seed_dev_data      # OPTIONAL: synthetic history so the UI has something to show
uvicorn api.main:app --reload --port 8000
```

`/api/health` reports `degraded` and the *Run* menu returns a clear error when Redis/Celery are not running — start Redis,
then `celery -A scheduler.celery_app worker --loglevel=info` and `celery -A scheduler.celery_app beat --loglevel=info`
to enable crawling and scheduled alert checks.

### Frontend

```bash
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev      # http://localhost:3000 (proxies /api to the backend)
```

If port 8000 is taken, point `BACKEND_URL` at wherever uvicorn is running.

## Database & migrations

Schema is managed by Alembic (`db/migrations/versions`).

```bash
alembic upgrade head        # apply
alembic downgrade -1        # roll back one revision
alembic revision --autogenerate -m "describe change"
alembic check               # fails if models and migrations drift
```

Docker: migrations run automatically when the `app` container starts. Backups:

```bash
docker compose exec postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < backup.sql
```

## Tests and quality checks

```bash
# Backend
pytest                      # 32 tests: API, CRUD, parsers, validators, pipeline
ruff check .                # lint

# Frontend
cd frontend
npm test                    # vitest (11 tests)
npm run lint                # eslint
npm run build               # production bundle
```

## Production deployment

1. Provision Postgres and Redis (managed services are fine). Set `APP_ENV=production`, a strong `API_KEY`,
   real database credentials and `CORS_ORIGINS` in the environment (not in git).
2. Build and run the images: `docker compose up --build -d`. The API docs (`/docs`) are disabled in production.
3. Put a TLS-terminating reverse proxy (Caddy, Traefik, a cloud load balancer) in front of the `frontend` container.
   The bundled nginx forwards `/api/` to the API, so the browser uses a single origin.
4. Keep Postgres, Redis and Flower off the public internet (Postgres and Redis are not published by the compose file; Flower binds to `127.0.0.1`).
5. Roll out upgrades with `docker compose pull && docker compose up --build -d`; migrations apply on boot. Take a
   `pg_dump` first.
6. Optional: serve the frontend from a static host instead — build with `VITE_API_BASE_URL=https://api.example.com/api`
   and add that site to `CORS_ORIGINS`.

## How to…

- **Track a new model:** add an ASIN in *Products → Track product*, or add a query to `search_queries` in
  `config/settings.py` (or `SEARCH_QUERIES` env, comma-separated) and run *Discover products*.
- **Add PIN codes:** extend `TAMIL_NADU_PINCODES` and `PINCODE_TO_IP` in `anti_bot/geo_simulator.py`.
- **Change alert sensitivity:** *Settings → Alert thresholds* (default or per-ASIN).

## Known limitations

- **Seller offers (all sellers per product) are not collected yet.** Amazon retired the offer-listing page this
  job reads and now loads "Other sellers" dynamically, and many bearing listings have a single seller anyway. The
  product refresh still records the Buy Box seller, price, MRP and stock on every run, which drives the Buy Box and
  price-drop alerts. For complete offer data consider Amazon's Product Advertising API or a headless-browser job.

- Amazon markup changes frequently; parsers in `data_pipeline/parser.py` use selectors that may need maintenance, and
  real crawls were **not** executed in development (no proxy credentials / network scraping in CI).
- Authentication is a single shared API key (no per-user accounts or roles).
- The legacy Streamlit dashboard is kept for compatibility but is not part of the main UI and has not been re-verified
  in every environment.
