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
The CSV is baked into the image, so `POST /load/revenues/demo` works with no upload.

## Project layout

```
box_office/
  config.py            # paths, DB URL, OMDb key (from env)
  db.py                # engine, session, init_db()
  models/
    base.py            # DwhTable base (load_timestamp audit column)
    bronze.py          # raw landing tables
    dimensions.py      # dim_date, dim_movie (SCD2), dim_distributor, ...
    facts.py           # fact_daily_revenue, fact_movie_rating
    bridges.py         # bridge_movie_genre, bridge_movie_person
data/                  # warehouse.db (git-ignored)
docs/                  # ER diagram
```

## Model at a glance

- **Facts:** `fact_daily_revenue` (transaction, film×day) and `fact_movie_rating`
  (periodic snapshot, film×source×snapshot).
- **Dimensions:** `dim_date`, `dim_movie` (**SCD Type 2** on distributor),
  `dim_distributor`, `dim_rating_source`, `dim_genre`, `dim_person`.
- **Bridges:** `bridge_movie_genre`, `bridge_movie_person`.
- **Keys:** every key uses the `_id` suffix; a FK carries the same name as the
  PK it references. `dim_movie` has `movie_version_id` (version PK, point-in-time)
  and `movie_id` (durable, used by ratings/bridges).
