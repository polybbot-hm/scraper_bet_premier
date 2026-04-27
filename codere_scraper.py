"""
Scraper Codere — misma lógica que SportsbookScraperAPI/adapters/outbound/scrapers/codere_scraper.py.

Por defecto el CLI filtra la Premier League; la clase acepta cualquier `league_name`.
"""
from __future__ import annotations

import re
import time
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional, Sequence, Set

from http_client import get_with_retry
from models import (
    BookmakerName,
    CODERE_CATEGORY_MAP,
    DEFAULT_TARGET_CATEGORIES,
    Event,
    MarketType,
    OddsSnapshot,
)


def _fold_for_substring_match(text: str) -> str:
    """Minúsculas + quita marcas diacríticas para que 'urvalsdeild' case con 'Úrvalsdeild'."""
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return without_marks.lower()


def _exclude_leagues_by_name(leagues: list, patterns: Optional[Sequence[str]]) -> list:
    """Quita ligas cuyo Name contiene alguna subcadena (case-insensitive, sin tildes)."""
    if not patterns:
        return leagues
    pl = [_fold_for_substring_match(p) for p in patterns if p and str(p).strip()]
    if not pl:
        return leagues
    kept = []
    for league in leagues:
        name = _fold_for_substring_match(league.get("Name") or "")
        if any(sub in name for sub in pl):
            continue
        kept.append(league)
    return kept


BASE_URL = "https://m.apuestas.codere.es/NavigationService"
REFERER = "https://m.apuestas.codere.es/"

_FOULS_KEYWORD = "falt"

_DOTNET_DATE_RE = re.compile(r"/Date\((-?\d+)")


def _parse_dotnet_date(value: str | None) -> datetime | None:
    if not value:
        return None
    m = _DOTNET_DATE_RE.search(value)
    if not m:
        return None
    ms = int(m.group(1))
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).replace(tzinfo=None)


def _extract_event_date(ev: dict) -> datetime | None:
    for field in ("StartDate", "StarDate", "StartDateFormatted"):
        result = _parse_dotnet_date(ev.get(field))
        if result is not None:
            return result
    return None


class CodereScraper:
    """
    Scraper para Codere (API móvil).
    Categorías configurables; por defecto DEFAULT_TARGET_CATEGORIES.
    """

    def __init__(self, session=None, target_categories: Optional[Set[MarketType]] = None):
        self._session = session
        self._target_categories = target_categories or DEFAULT_TARGET_CATEGORIES

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        url = f"{BASE_URL}/{path}"
        r = get_with_retry(url, session=self._session, params=params, referer=REFERER)
        r.raise_for_status()
        return r.json()

    def scrape_fouls_markets(
        self,
        league_name: Optional[str] = None,
        sport_handle: str = "soccer",
        exclude_league_substrings: Optional[Sequence[str]] = None,
    ) -> List[OddsSnapshot]:
        """Mercados de FALTAS (ESTADÍSTICAS + nombre con 'falt')."""
        snapshots = self.scrape_markets(
            league_name=league_name,
            sport_handle=sport_handle,
            target_categories={MarketType.ESTADISTICAS},
            exclude_league_substrings=exclude_league_substrings,
        )
        return [s for s in snapshots if s.market_type == MarketType.FALTAS]

    def scrape_markets(
        self,
        league_name: Optional[str] = None,
        sport_handle: str = "soccer",
        target_categories: Optional[Set[MarketType]] = None,
        exact_league_match: bool = False,
        exclude_league_substrings: Optional[Sequence[str]] = None,
    ) -> List[OddsSnapshot]:
        cats_to_scrape = target_categories or self._target_categories

        sports = self._get("Home/GetSports")
        sport = next((s for s in sports if s.get("SportHandle") == sport_handle), None)
        if not sport:
            return []

        countries = self._get(
            "Home/GetCountriesByDate",
            params={"sportHandle": sport_handle, "nodeId": sport["NodeId"]},
        )
        leagues = []
        for country in countries or []:
            leagues.extend(country.get("Leagues", []))

        if league_name:
            if exact_league_match:
                needle = league_name.strip().lower()
                leagues = [
                    l for l in leagues if l.get("Name", "").strip().lower() == needle
                ]
            else:
                needle = league_name.lower()
                leagues = [l for l in leagues if needle in l.get("Name", "").lower()]
        leagues = _exclude_leagues_by_name(leagues, exclude_league_substrings)
        if not leagues:
            return []

        results: List[OddsSnapshot] = []
        now = datetime.utcnow()

        for league in leagues:
            league_node_id = league["NodeId"]
            events_data = self._get(
                "Event/GetMultipleEventsByDate",
                params={
                    "utcOffsetHours": 1,
                    "dayDifference": 0,
                    "parentids": league_node_id,
                    "gametypes": "1;18",
                },
            )
            events_list = (
                events_data.get(str(league_node_id), [])
                if isinstance(events_data, dict)
                else []
            )

            for ev in events_list:
                participants = ev.get("Participants", [])
                if len(participants) < 2:
                    continue
                home = (
                    participants[0]
                    .get("LocalizedNames", {})
                    .get("LocalizedValues", [{}])[0]
                    .get("Value", "Local")
                )
                away = (
                    participants[1]
                    .get("LocalizedNames", {})
                    .get("LocalizedValues", [{}])[0]
                    .get("Value", "Visitante")
                )
                event_node_id = ev.get("NodeId")

                event = Event(
                    external_id=str(event_node_id),
                    home_team=home,
                    away_team=away,
                    league_name=league.get("Name", ""),
                    sport=sport_handle,
                    event_date=_extract_event_date(ev),
                )

                cat_data = self._get(
                    "Game/GetGamesNoLiveAndCategoryInfos",
                    params={"parentid": event_node_id},
                )
                cat_list = (
                    cat_data.get("CategoriesInformation", [])
                    if isinstance(cat_data, dict)
                    else []
                )

                for cat in cat_list:
                    cat_name_raw = (cat.get("CategoryName") or "").strip()
                    cat_name_clean = (
                        cat_name_raw.encode("ascii", "ignore").decode().strip()
                    )
                    market_type = CODERE_CATEGORY_MAP.get(
                        cat_name_raw
                    ) or CODERE_CATEGORY_MAP.get(cat_name_clean)

                    if market_type not in cats_to_scrape:
                        continue

                    time.sleep(0.2)
                    markets_raw = self._get(
                        "Game/GetGamesNoLiveByCategoryInfo",
                        params={
                            "parentid": event_node_id,
                            "categoryInfoId": cat["CategoryId"],
                        },
                    )
                    markets_list = markets_raw if isinstance(markets_raw, list) else []

                    for mercado in markets_list:
                        market_name = mercado.get("Name", "")

                        effective_type = market_type
                        if (
                            market_type == MarketType.ESTADISTICAS
                            and _FOULS_KEYWORD in market_name.lower()
                        ):
                            effective_type = MarketType.FALTAS

                        for result_item in mercado.get("Results", []):
                            selection = result_item.get("Name", "")
                            try:
                                odd_val = Decimal(str(result_item.get("Odd", 0)))
                            except Exception:
                                odd_val = Decimal("0")

                            results.append(
                                OddsSnapshot(
                                    event=event,
                                    market_name=market_name,
                                    market_type=effective_type,
                                    selection_name=selection,
                                    odds_value=odd_val,
                                    bookmaker=BookmakerName.CODERE,
                                    scraped_at=now,
                                )
                            )

        return results
