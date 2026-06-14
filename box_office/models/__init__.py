"""Importing this package registers all tables on SQLModel.metadata."""

from .bridges import (
    BridgeMovieCountry,
    BridgeMovieGenre,
    BridgeMovieLanguage,
    BridgeMoviePerson,
)
from .bronze import BronzeOmdbRaw, BronzeRevenueCsv
from .dimensions import (
    DimCountry,
    DimDate,
    DimDistributor,
    DimGenre,
    DimLanguage,
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
    "DimLanguage",
    "DimCountry",
    "DimPerson",
    "DimMovie",
    "FactDailyRevenue",
    "FactMovieRating",
    "BridgeMovieGenre",
    "BridgeMoviePerson",
    "BridgeMovieLanguage",
    "BridgeMovieCountry",
]
