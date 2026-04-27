-- Ejecutar en Supabase → SQL Editor.
-- Misma forma desnormalizada que SportsbookScraperAPI (odds_raw), tabla separada para este scraper.

CREATE TABLE IF NOT EXISTS premier_odds_raw (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_event_id   text NOT NULL,
    partido             text NOT NULL,
    home_team           text NOT NULL,
    away_team           text NOT NULL,
    liga                text NOT NULL,
    sport               text NOT NULL DEFAULT 'soccer',
    bookmaker           text NOT NULL,
    categoria           text NOT NULL,
    mercado             text NOT NULL,
    selection           text NOT NULL,
    cuota               numeric(10, 4) NOT NULL,
    event_date          timestamptz,
    scraped_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_premier_odds_raw_event
    ON premier_odds_raw (external_event_id);
CREATE INDEX IF NOT EXISTS idx_premier_odds_raw_bookmaker
    ON premier_odds_raw (bookmaker);
CREATE INDEX IF NOT EXISTS idx_premier_odds_raw_liga
    ON premier_odds_raw (liga);
CREATE INDEX IF NOT EXISTS idx_premier_odds_raw_scraped
    ON premier_odds_raw (scraped_at DESC);

-- Si activas RLS, añade políticas para tu clave (anon) o usa service_role, que bypass RLS.
