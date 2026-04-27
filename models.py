"""Modelos alineados con SportsbookScraperAPI (subset Codere)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class BookmakerName(str, Enum):
    CODERE = "codere"


class MarketType(str, Enum):
    FALTAS = "faltas"
    PRINCIPALES = "principales"
    ESTADISTICAS = "estadisticas"
    TIROS = "tiros"
    CORNERS = "corners"
    HANDICAP = "handicap"
    RESULTADO_FINAL = "resultado_final"
    EQUIPOS = "equipos"
    TARJETAS = "tarjetas"
    GOLES = "goles"
    GOLEADORES = "goleadores"
    PRIMERA_SEGUNDA_PARTE = "primera_segunda_parte"
    ESPECIALES = "especiales"
    ASISTENCIAS = "asistencias"
    PASES = "pases"
    ENTRADAS = "entradas"
    MINUTOS = "minutos"
    COMBINADOS = "combinados"
    MATCHACCA = "matchacca"


CODERE_CATEGORY_MAP: dict[str, MarketType] = {
    "PRINCIPALES": MarketType.PRINCIPALES,
    "ESTADÍSTICAS": MarketType.ESTADISTICAS,
    "ESTADISTICAS": MarketType.ESTADISTICAS,
    "TIROS": MarketType.TIROS,
    "CORNERS": MarketType.CORNERS,
    "HANDICAP": MarketType.HANDICAP,
    "RES. FINAL": MarketType.RESULTADO_FINAL,
    "EQUIPOS": MarketType.EQUIPOS,
    "TARJETAS": MarketType.TARJETAS,
    "GOLES": MarketType.GOLES,
    "GOLEADORES": MarketType.GOLEADORES,
    "1ª/2ª PARTE": MarketType.PRIMERA_SEGUNDA_PARTE,
    "ESPECIALES": MarketType.ESPECIALES,
    "ASISTENCIAS": MarketType.ASISTENCIAS,
    "PASES": MarketType.PASES,
    "ENTRADAS": MarketType.ENTRADAS,
    "MINUTOS": MarketType.MINUTOS,
    "COMBINADOS": MarketType.COMBINADOS,
    "MATCHACCA": MarketType.MATCHACCA,
}

DEFAULT_TARGET_CATEGORIES: set[MarketType] = {
    MarketType.PRINCIPALES,
    MarketType.ESTADISTICAS,
    MarketType.CORNERS,
    MarketType.HANDICAP,
    MarketType.RESULTADO_FINAL,
    MarketType.EQUIPOS,
}


@dataclass(frozen=True)
class Event:
    external_id: str
    home_team: str
    away_team: str
    league_name: str
    sport: str
    event_date: Optional[datetime] = None

    @property
    def match_label(self) -> str:
        return f"{self.home_team} vs {self.away_team}"


@dataclass
class OddsSnapshot:
    event: Event
    market_name: str
    market_type: MarketType
    selection_name: str
    odds_value: Decimal
    bookmaker: BookmakerName
    scraped_at: datetime
