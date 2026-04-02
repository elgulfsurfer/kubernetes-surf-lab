CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- NOAA buoy stations
CREATE TABLE buoys (
    id          SERIAL PRIMARY KEY,
    station_id  TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Surf spots
CREATE TABLE spots (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Many-to-many: spots <-> buoys
CREATE TABLE spot_buoys (
    spot_id     INT NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    buoy_id     INT NOT NULL REFERENCES buoys(id) ON DELETE CASCADE,
    PRIMARY KEY (spot_id, buoy_id)
);

-- Many-to-many: users <-> spots
CREATE TABLE user_spots (
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spot_id     INT NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, spot_id)
);

-- Boards (max 10 per user, no hard deletes)
CREATE TABLE boards (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    brand       TEXT,
    model       TEXT,
    length      NUMERIC(5,2) NOT NULL,
    width       NUMERIC(5,2) NOT NULL,
    height      NUMERIC(5,2) NOT NULL,
    volume      NUMERIC(5,2),
    type        TEXT NOT NULL CHECK (type IN (
                    'Shortboard','Groveler','Fish','Step Up','Gun',
                    'SUP','Mid-Length','Fun Board','Longboard','Soft Top','Boogie')),
    fin_setup   TEXT NOT NULL CHECK (fin_setup IN (
                    'Single','Twin','Thruster','Quad','5-Fin','Finless')),
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Session logs (soft delete)
CREATE TABLE logs (
    id                  SERIAL PRIMARY KEY,
    user_id             INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    spot_id             INT NOT NULL REFERENCES spots(id),
    board_id            INT NOT NULL REFERENCES boards(id),
    name                TEXT,
    date                DATE NOT NULL,
    start_time          TIME NOT NULL,
    end_time            TIME NOT NULL,
    forecaster          TEXT NOT NULL CHECK (forecaster IN ('Surfline','SurfReport','Other')),
    forecaster_accuracy INT NOT NULL CHECK (forecaster_accuracy BETWEEN 1 AND 10),
    quality             INT NOT NULL CHECK (quality BETWEEN 1 AND 10),
    fun                 INT NOT NULL CHECK (fun BETWEEN 1 AND 10),
    crowd_level         INT NOT NULL CHECK (crowd_level BETWEEN 1 AND 5),
    board_quality       INT NOT NULL CHECK (board_quality BETWEEN 1 AND 10),
    description         TEXT NOT NULL CHECK (
                            char_length(description) >= 20 AND
                            char_length(description) <= 200),
    deleted_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Buoy data (7-day rolling window)
CREATE TABLE buoy_data (
    id              SERIAL PRIMARY KEY,
    buoy_id         INT NOT NULL REFERENCES buoys(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    wave_height     NUMERIC(5,2),
    wave_period     NUMERIC(5,2),
    wave_direction  NUMERIC(5,2),
    water_temp      NUMERIC(5,2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (buoy_id, date)
);

CREATE INDEX idx_spot_buoys_buoy ON spot_buoys(buoy_id);

CREATE INDEX idx_logs_user_id  ON logs(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_logs_spot_id  ON logs(spot_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_buoy_buoy_date ON buoy_data(buoy_id, date);
