-- En Neon, ejecutar esto primero

DO $$ BEGIN
    CREATE TYPE promo_type_enum AS ENUM ('percent', 'two_for');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE stock_status_enum AS ENUM ('available', 'low', 'out');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    pid VARCHAR(24) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    winery VARCHAR(120),
    varietal VARCHAR(80),
    year INT,
    photo_url TEXT,
    price_list NUMERIC(10,2) NOT NULL,
    promo_type promo_type_enum,
    promo_value NUMERIC(10,2),
    promo_valid_from TIMESTAMPTZ,
    promo_valid_to TIMESTAMPTZ,
    stock_status stock_status_enum NOT NULL DEFAULT 'available',
    description TEXT
);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_pid ON products(pid);
