"""
Persistencia en Supabase (supabase-py), alineada con
SportsbookScraperAPI `SupabaseClientRepository._snapshot_to_row` / `save_snapshots`.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models import OddsSnapshot

DEFAULT_TABLE = "premier_odds_raw"


def snapshot_to_row(s: "OddsSnapshot") -> dict:
    row = {
        "external_event_id": s.event.external_id,
        "partido": s.event.match_label,
        "home_team": s.event.home_team,
        "away_team": s.event.away_team,
        "liga": s.event.league_name,
        "sport": s.event.sport,
        "bookmaker": s.bookmaker.value,
        "categoria": s.market_type.value,
        "mercado": s.market_name,
        "selection": s.selection_name,
        "cuota": float(s.odds_value),
        "scraped_at": s.scraped_at.isoformat(),
    }
    if s.event.event_date is not None:
        row["event_date"] = s.event.event_date.isoformat()
    return row


def save_snapshots(
    snapshots: List["OddsSnapshot"],
    *,
    supabase_url: str,
    supabase_key: str,
    table: str = DEFAULT_TABLE,
    batch_size: int = 500,
) -> int:
    """Inserta todas las filas; devuelve número de snapshots guardadas."""
    if not snapshots:
        return 0
    from supabase import create_client

    client = create_client(supabase_url, supabase_key)
    rows = [snapshot_to_row(s) for s in snapshots]
    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        client.table(table).insert(chunk).execute()
    return len(rows)


def load_settings_from_env() -> tuple[str | None, str | None, str]:
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    table = os.environ.get("SUPABASE_PREMIER_TABLE", DEFAULT_TABLE)
    return (url, key, table)
