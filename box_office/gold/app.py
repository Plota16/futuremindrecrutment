"""Gold layer — Streamlit ranking dashboards (read-only over the warehouse).

Run:  streamlit run box_office/gold/app.py

Each ranking is computed in SQL by GoldQueries; this module only picks inputs
(the year) and renders the resulting DataFrames as a table + chart.
"""

from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from box_office.constants import CREDIT_ACTOR, CREDIT_DIRECTOR
from box_office.db import engine
from box_office.gold.queries import GoldQueries

st.set_page_config(page_title="Box Office Rankings", layout="wide")
st.title("🎬 Box Office — Ranking Dashboards")


# Cached data loaders (one short-lived session per query).

@st.cache_data(ttl=60)
def available_years() -> list[int]:
    try:
        with Session(engine) as s:
            return GoldQueries(s).available_years()
    except (OperationalError, pd.errors.DatabaseError):
        return []


@st.cache_data(ttl=60)
def top_movies(year: int) -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_movies_by_year(year)


@st.cache_data(ttl=60)
def top_movies_all_time() -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_movies_all_time()


@st.cache_data(ttl=60)
def top_role(role: str) -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_by_role(role)


@st.cache_data(ttl=60)
def top_theaters() -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_theaters_peak(3)


@st.cache_data(ttl=60)
def top_rated() -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_rated_movies()


@st.cache_data(ttl=60)
def top_holidays() -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_holidays()


@st.cache_data(ttl=60)
def revenue_by_daytype() -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).revenue_by_daytype()


@st.cache_data(ttl=60)
def top_countries(min_movies: int) -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_countries_by_rating(min_movies=min_movies)


@st.cache_data(ttl=60)
def top_genres(min_movies: int) -> pd.DataFrame:
    with Session(engine) as s:
        return GoldQueries(s).top_genres_by_rating(min_movies=min_movies)


# Rendering helpers.

def render_ranking(df: pd.DataFrame, label_col: str, value_col: str,
                   money_col: str | None = None) -> None:
    if df.empty:
        st.info("No data for this view.")
        return
    table, chart = st.columns([1, 1])
    with table:
        display = df.copy()
        # Revenue is whole USD; the chart keeps the numeric column.
        if money_col:
            display[money_col] = display[money_col].map(
                lambda v: f"${v:,.0f}")
        st.dataframe(display, hide_index=True, width='stretch')
    with chart:
        st.bar_chart(df.set_index(label_col)[value_col])


def render_pie(df: pd.DataFrame, category_col: str, value_col: str) -> None:
    if df.empty:
        st.info("No data for this view.")
        return
    table, chart = st.columns([1, 1])
    with table:
        display = df.copy()
        total = display[value_col].sum()
        display["share"] = display[value_col].map(
            lambda v: f"{v / total * 100:.1f}%") if total else "—"
        display[value_col] = display[value_col].map(lambda v: f"${v:,.0f}")
        st.dataframe(display, hide_index=True, width='stretch')
    with chart:
        pie = (
            alt.Chart(df)
            .mark_arc(innerRadius=60)
            .encode(
                theta=alt.Theta(f"{value_col}:Q", stack=True),
                color=alt.Color(f"{category_col}:N", title=None),
                tooltip=[category_col,
                         alt.Tooltip(f"{value_col}:Q", format="$,.0f")],
            )
        )
        st.altair_chart(pie, width='stretch')


# Page.

years = available_years()
if not years:
    st.warning(
        "No data yet — run the ETL first (e.g. POST /load/all)."
    )
    st.stop()

(
    by_year_tab,
    all_time_tab,
    actors_tab,
    directors_tab,
    theaters_tab,
    rated_tab,
    holidays_tab,
    daytype_tab,
    countries_tab,
    genres_tab,
) = st.tabs(
    [
        "Movies by year",
        "Box office all-time",
        "Actors",
        "Directors",
        "Theaters (peak)",
        "Top rated",
        "Top holidays",
        "Weekend/Holiday vs Weekday",
        "Countries by rating",
        "Genres by rating",
    ]
)

with by_year_tab:
    st.subheader("Top 5 — box office revenue by year")
    current = date.today().year
    default_idx = years.index(current) if current in years else 0
    year = st.selectbox("Year", years, index=default_idx)
    render_ranking(top_movies(year), label_col="title", value_col="box_office",
                   money_col="box_office")

with all_time_tab:
    st.subheader("Top 5 — box office revenue all-time")
    render_ranking(top_movies_all_time(), label_col="title",
                   value_col="box_office", money_col="box_office")

with actors_tab:
    st.subheader("Top 5 actors — combined box office of their films")
    render_ranking(top_role(CREDIT_ACTOR), label_col="name",
                   value_col="box_office", money_col="box_office")

with directors_tab:
    st.subheader("Top 5 directors — combined box office of their films")
    render_ranking(top_role(CREDIT_DIRECTOR), label_col="name",
                   value_col="box_office", money_col="box_office")

with theaters_tab:
    st.subheader("Top 5 movies by peak theater count (with the peak day)")
    render_ranking(top_theaters(), label_col="title", value_col="theaters")

with rated_tab:
    st.subheader(
        "Top 5 rated movies — mean score (0-100), native per-source"
    )
    render_ranking(top_rated(), label_col="title", value_col="avg_score")

with holidays_tab:
    st.subheader("Top 5 most profitable holidays")
    render_ranking(top_holidays(), label_col="holiday", value_col="box_office",
                   money_col="box_office")

with daytype_tab:
    st.subheader("Box office share — Weekend/Holiday vs Weekday")
    render_pie(revenue_by_daytype(), category_col="day_type",
               value_col="box_office")

with countries_tab:
    st.subheader("Countries — best average rating (0-100, normalized)")
    min_c = st.slider(
        "Minimum rated films per country", 1, 10, 2, key="min_c"
    )
    df_c = top_countries(min_c)
    if df_c.empty:
        st.info(
            "No country has enough rated films yet. "
            "Lower the minimum or run the OMDb enrichment first."
        )
    else:
        render_ranking(df_c, label_col="country", value_col="avg_score")

with genres_tab:
    st.subheader("Genres — best average rating (0-100, normalized)")
    min_g = st.slider(
        "Minimum rated films per genre", 1, 10, 2, key="min_g"
    )
    df_g = top_genres(min_g)
    if df_g.empty:
        st.info(
            "No genre has enough rated films yet. "
            "Lower the minimum or run the OMDb enrichment first."
        )
    else:
        render_ranking(df_g, label_col="genre", value_col="avg_score")
