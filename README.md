# Box Office Data Warehouse

Design notes (ER diagram, medallion/SCD decisions) live in
[`docs/er_diagram.html`](docs/er_diagram.html).

## How to run it

You need a free OMDb API key: https://www.omdbapi.com/apikey.aspx

### Docker (recommended)

```bash
cp .env.example .env          # put your OMDB_API_KEY here
docker compose up --build
```

- **API** → http://localhost:8000/docs
- **Dashboard** → http://localhost:8501

The schema is created on startup and `data/warehouse.db` is persisted via a
volume. The CSV is baked into the image, so the load endpoints work with no
upload. The dashboard shows a "run the ETL" notice until data is loaded.

### Local

```bash
poetry install
export OMDB_API_KEY=your_key

# API (schema is created on startup)
poetry run uvicorn box_office.api.main:app --reload      # http://127.0.0.1:8000/docs

# Dashboard (separate terminal)
poetry run streamlit run box_office/gold/app.py          # http://localhost:8501
```

## Loading the data

All load endpoints are `POST`. Call them from `/docs` or with `curl`.

| Endpoint | What it does |
|----------|--------------|
| `POST /load/all` | Run everything end to end (CSV + OMDb + silver). |
| `POST /load/csv` | Land the CSV into bronze (fast, no API). Omit the upload to use the bundled CSV. |
| `POST /load/omdb?omdb_limit=N` | Fetch OMDb data, **highest-earning titles first**. Resumable — each run only fetches what's still missing. |
| `POST /load/silver` | Rebuild the silver model from the **current** bronze state. |
| `POST /refresh/movies?scope=stale` | Re-snapshot ratings for movies whose data has gone stale. |

### Simple case — full load

If the OMDb daily quota isn't a concern, just run one call and **omit
`omdb_limit`** (no limit = fetch everything):

```bash
curl -X POST http://localhost:8000/load/all
```

### Quota-limited case — step by step

OMDb's free tier caps at **1,000 calls/day**. Drain the backlog over several
days while keeping the revenue rankings live from day one:

1. `POST /load/csv` — land the CSV (no API calls).
2. `POST /load/silver` — build the revenue/theater/holiday rankings immediately
   (these need no OMDb data).
3. `POST /load/omdb?omdb_limit=1000` — fetch today's batch (top earners first).
4. `POST /load/silver` — rebuild silver so the newly enriched movies get their
   ratings/genres/cast.
5. Repeat **3–4 once per day** until everything is enriched.
6. Later, keep ratings fresh with `POST /refresh/movies?scope=stale`.
