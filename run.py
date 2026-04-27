"""CLI: Codere — Premier League (por defecto). Ejecutar desde esta carpeta o vía `python run.py`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from codere_scraper import CodereScraper  # noqa: E402

# Coincide con "Premier League - Urvalsdeild Karla" (Islandia); no la Premier inglesa.
DEFAULT_EXCLUDE_LEAGUE_SUBSTRINGS = ("urvalsdeild",)


def _snapshot_dict(s):
    ev = s.event
    return {
        "match": ev.match_label,
        "league": ev.league_name,
        "event_id": ev.external_id,
        "event_date": ev.event_date.isoformat() if ev.event_date else None,
        "market_name": s.market_name,
        "market_type": s.market_type.value,
        "selection": s.selection_name,
        "odds": float(s.odds_value),
        "bookmaker": s.bookmaker.value,
        "scraped_at": s.scraped_at.isoformat(),
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="Scrape Codere (API móvil) filtrando por liga; por defecto Premier League."
    )
    p.add_argument(
        "--all-leagues",
        action="store_true",
        help="No filtrar por nombre de liga (recorre todas las competiciones de fútbol del día).",
    )
    p.add_argument(
        "--league",
        default="premier",
        help='Subcadena para filtrar ligas (default: "premier"). Ignorado si --all-leagues.',
    )
    p.add_argument(
        "--exact-league",
        action="store_true",
        help="Coincidencia exacta del nombre de liga con --league.",
    )
    p.add_argument(
        "--exclude-league",
        action="append",
        default=None,
        metavar="SUBCADENA",
        help=(
            "Omite ligas cuyo nombre contiene esta subcadena (sin distinguir mayúsculas). "
            "Repetible. Por defecto se excluye 'urvalsdeild' (p. ej. Premier islandesa); "
            "usa --no-default-excludes para quitar eso."
        ),
    )
    p.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="No aplicar exclusiones por defecto (urvalsdeild).",
    )
    p.add_argument("--sport", default="soccer", help="SportHandle Codere (default: soccer).")
    p.add_argument(
        "--fouls-only",
        action="store_true",
        help="Solo mercados de faltas (misma lógica que scrape_fouls_markets).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Ruta JSON de salida (lista de cuotas). Si se omite, imprime resumen.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Máximo de snapshots a volcar en consola/JSON (0 = sin límite). No recorta lo enviado a Supabase.",
    )
    p.add_argument(
        "--skip-supabase",
        action="store_true",
        help="No insertar en Supabase aunque existan SUPABASE_URL y SUPABASE_KEY.",
    )
    p.add_argument(
        "--supabase-only",
        action="store_true",
        help="Solo persistir en BD: no escribe JSON ni imprime el listado largo (sí muestra resumen).",
    )
    args = p.parse_args()
    load_dotenv(_ROOT / ".env")

    if args.supabase_only and args.skip_supabase:
        print("Combina --supabase-only con --skip-supabase: elige uno.", file=sys.stderr)
        return 2

    if args.all_leagues:
        league = None
    else:
        league = (args.league or "").strip() or None

    exclude_patterns: list[str] = []
    if not args.no_default_excludes:
        exclude_patterns.extend(DEFAULT_EXCLUDE_LEAGUE_SUBSTRINGS)
    if args.exclude_league:
        exclude_patterns.extend(args.exclude_league)
    exclude_tuple = tuple(dict.fromkeys(p.strip().lower() for p in exclude_patterns if p.strip()))

    scraper = CodereScraper()

    if args.fouls_only:
        rows = scraper.scrape_fouls_markets(
            league_name=league,
            sport_handle=args.sport,
            exclude_league_substrings=exclude_tuple or None,
        )
    else:
        rows = scraper.scrape_markets(
            league_name=league,
            sport_handle=args.sport,
            exact_league_match=args.exact_league,
            exclude_league_substrings=exclude_tuple or None,
        )

    if args.limit > 0:
        out_rows = rows[: args.limit]
    else:
        out_rows = rows

    if not args.skip_supabase and rows:
        from supabase_persist import load_settings_from_env, save_snapshots

        url, key, table = load_settings_from_env()
        if url and key:
            try:
                n = save_snapshots(rows, supabase_url=url, supabase_key=key, table=table)
                print(f"Supabase: insertadas {n} filas en {table!r}")
            except Exception as exc:
                print(f"Supabase: error al insertar — {exc}", file=sys.stderr)
                return 1
        elif args.supabase_only:
            print(
                "Supabase: faltan SUPABASE_URL y SUPABASE_KEY (o .env).",
                file=sys.stderr,
            )
            return 1

    if args.supabase_only:
        n_ev = len({s.event.external_id for s in rows})
        print(f"Snapshots scrapeados: {len(rows)} | partidos únicos: {n_ev}")
        return 0 if rows else 0

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as f:
            json.dump([_snapshot_dict(s) for s in out_rows], f, ensure_ascii=False, indent=2)
        print(f"Guardado: {args.out} ({len(out_rows)} filas)")
        return 0

    print(f"Snapshots: {len(rows)}")
    if not rows:
        return 0
    n_events = len({s.event.external_id for s in rows})
    print(f"Partidos (eventos únicos): {n_events}")
    by_type: dict[str, int] = {}
    for s in rows:
        k = s.market_type.value
        by_type[k] = by_type.get(k, 0) + 1
    print("Por market_type:", json.dumps(by_type, ensure_ascii=False))
    for s in out_rows[:20]:
        ev = s.event
        print(f"  [{ev.match_label}] {s.market_name} | {s.selection_name} @ {s.odds_value}")
    if len(out_rows) > 20:
        print(f"  ... y {len(out_rows) - 20} más (usa --out o --limit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
