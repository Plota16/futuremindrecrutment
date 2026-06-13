"""Importing this package registers all tables on SQLModel.metadata."""

from .bridges import BridgeMovieGenre, BridgeMoviePerson
from .bronze import BronzeOmdbRaw, BronzeRevenueCsv
from .dimensions import (
    DimDate,
    DimDistributor,
    DimGenre,
    DimMovie,
    DimPerson,
    DimRatingSource,
)
from .facts import FactDailyRevenue, FactMovieRating

__all__ = [
    "BronzeRevenueCsv",
    "BronzeOmdbRaw",
    "DimDate",
    "DimDistributor",
    "DimRatingSource",
    "DimGenre",
    "DimPerson",
    "DimMovie",
    "FactDailyRevenue",
    "FactMovieRating",
    "BridgeMovieGenre",
    "BridgeMoviePerson",
]
