# scraper_premier_bet

Scraper de **Codere** (API móvil) orientado a **Premier League**. Opcional: volcado a **Supabase** (`premier_odds_raw`).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # y rellena Supabase si lo usas
```

Tabla SQL: `schema/premier_odds_raw.sql`

## Uso

```bash
python run.py
```

- Por defecto filtra ligas con `"premier"` y excluye la Premier islandesa (`urvalsdeild`).
- `dayDifference: 0` (un solo día en Codere).

Flags útiles: `--skip-supabase`, `--out archivo.json`, `--fouls-only`, `--all-leagues`, `--exclude-league`, `--no-default-excludes`.

## Requisitos

Python 3.10+ (aprox.). Credenciales solo en `.env` (no subir al repo).
