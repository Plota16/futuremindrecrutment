# Box Office Data Warehouse

FutureMind recruitment task — ingest `revenues_per_day.csv`, enrich it with the
OMDb API, model it dimensionally (star schema) and expose a ranking dashboard.

The full design (ER diagram, SCD/medallion decisions, key conventions) lives in
[`docs/er_diagram.html`](docs/er_diagram.html).

## Stack

- **Python 3.12+**, **Poetry** for dependency/venv management
- **SQLModel** (SQLAlchemy + Pydantic) for the schema, **SQLite** as the engine
- **pandas** + **requests** + **holidays** for the pipeline
- **Streamlit** for the dashboard

## Setup

```bash
poetry install
export OMDB_API_KEY=your_key   # free key: https://www.omdbapi.com/apikey.aspx
```

## Create the warehouse schema

```bash
poetry run python -m box_office.db
```

This creates `data/warehouse.db` with all bronze + silver tables.

## Run the API

Locally:

```bash
poetry run uvicorn box_office.api.main:app --reload   # http://127.0.0.1:8000/docs
```

With Docker:

```bash
cp .env.example .env        # put your OMDB_API_KEY here
docker compose up --build   # http://127.0.0.1:8000/docs
```

The schema is created on startup; `data/warehouse.db` is persisted via a volume.
The CSV is baked into the image, so the load endpoints work with no upload.

## Loading (phased)

Loading is split into independent, idempotent, resumable phases so the dashboard
goes live immediately and API enrichment can backfill on its own cadence:

| Phase | Endpoint | What it does |
|-------|----------|--------------|
| 1 — ingest | `POST /load/csv` | Land the CSV into `bronze_revenue_csv` (fast, no API). Omit the file to use the bundled demo CSV. |
| 2 — enrich | `POST /load/omdb?omdb_limit=1000` | Fill the OMDb cache, **highest-earning titles first**. Resumable — each run only fetches what's still missing. |
| 3 — build | `POST /load/silver` | Rebuild silver from the **current** bronze state: revenue facts for all movies, plus ratings/genres/cast for those already enriched. |
| all-in-one | `POST /load/all` | Run all three for dev/demo (omit `omdb_limit` to ignore the daily quota). |

**Why phased.** Revenue facts depend only on the CSV, so Phase 1 + 3 make the
ranking usable at once. Movies with no API data yet are loaded as *inferred
members* (natural key only) — the Kimball pattern for early-arriving facts /
late-arriving dimensions — and their attributes/ratings backfill via Phase 2
overwrites (Type 1). OMDb's free tier caps at 1,000 calls/day, so in production
Phase 2 runs on a schedule (cron / Airflow / a task queue), `omdb_limit`-bounded,
draining the backlog over days; Phase 3 re-runs after each batch. `OMDB_MAX_WORKERS`
(default 8) tunes fetch concurrency. Re-snapshot ratings over time with
`POST /refresh/movies?scope=stale`.

## Project layout

Modules are grouped by role — clear what is a client, repo, helper or pipeline step:

```
box_office/
  config.py            # paths, DB URL, OMDb key (from env)
  db.py                # engine, session, init_db()
  models/              # data only — no logic
    base.py            #   DwhTable (load_timestamp audit column)
    bronze.py          #   raw landing tables
    dimensions.py      #   dim_date, dim_movie, dim_distributor, ...
    facts.py           #   fact_daily_revenue, fact_movie_rating
    bridges.py         #   bridge_movie_genre, bridge_movie_person
    omdb.py            #   OmdbResult, OmdbFetchStats, ParsedMovie, ParsedRating
    results.py         #   BronzeResult, SilverResult, RefreshResult
    api.py             #   request/response schemas
  clients/             # external API clients
    omdb.py            #   OmdbClient (HTTP)
  repositories/        # data access (DB / cache) — all reads/writes, no commits
    omdb.py            #   OmdbRepository (bronze_omdb_raw + client)
    revenue.py         #   RevenueRepository (bronze_revenue_csv)
    calendar.py        #   DateRepository (dim_date)
    reference.py       #   ReferenceRepository (distributor/genre/person/source)
    movies.py          #   MovieRepository (dim_movie + bridges)
    facts.py           #   FactRepository (fact tables)
  helpers/             # pure functions, no IO
    parsing.py         #   OMDb JSON -> ParsedMovie
  pipeline/            # ETL build steps + orchestrator
    calendar.py        #   dim_date
    reference.py       #   distributor/genre/person/source dims
    movies.py          #   dim_movie + bridges
    facts.py           #   fact builders
    etl.py             #   BoxofficeETL, bootstrap
  api/
    main.py            # FastAPI app (endpoints -> BoxofficeETL)
data/                  # warehouse.db (git-ignored)
docs/                  # ER diagram
```

## Model at a glance

- **Facts:** `fact_daily_revenue` (transaction, film×day) and `fact_movie_rating`
  (periodic snapshot, film×source×snapshot).
- **Dimensions:** `dim_date`, `dim_movie` (**SCD Type 1**, keyed by `title`),
  `dim_distributor`, `dim_rating_source`, `dim_genre`, `dim_person`.
- **Bridges:** `bridge_movie_genre`, `bridge_movie_person`.
- **Keys:** every key uses the `_id` suffix; a FK carries the same name as the
  PK it references. `dim_movie` uses `movie_id` as its durable surrogate PK
  (natural key: `title`), referenced by ratings and bridges.
