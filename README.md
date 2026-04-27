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

## Railway (cron)

Igual que en `scrapers_bookers`: repo con `Dockerfile` + `railway.json`, servicio **Cron**.

1. New project → deploy desde GitHub (este repo).
2. Variables del servicio: `SUPABASE_URL`, `SUPABASE_KEY` (service role recomendado). Opcional: `SUPABASE_PREMIER_TABLE`.
3. Cron por defecto: cada 3 h UTC (`0 */3 * * *` en `railway.json`); ajústalo en el panel si hace falta.

El job ejecuta `python run.py --supabase-only` (scrape + insert en Supabase, salida mínima en logs).

Prueba local de imagen:

```bash
docker build -t premier-codere .
docker run --rm -e SUPABASE_URL=... -e SUPABASE_KEY=... premier-codere
```
