-- ╔═══════════════════════════════════════════════════════════╗
-- ║   LotoMind Enterprise — Database Initialization          ║
-- ╚═══════════════════════════════════════════════════════════╝

CREATE SCHEMA IF NOT EXISTS lotomind;

SET search_path TO lotomind, public;

-- ── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL    PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'USER',
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Bets ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bets (
    id          BIGSERIAL     PRIMARY KEY,
    user_id     BIGINT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    numbers     INTEGER[]     NOT NULL,
    contest     INTEGER,
    strategy    VARCHAR(50),
    created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_numbers_count CHECK (array_length(numbers, 1) BETWEEN 15 AND 20)
);
-- ── Concursos (Lottery Results) ───────────────────────
CREATE TABLE IF NOT EXISTS concursos (
    id          BIGSERIAL    PRIMARY KEY,
    concurso    INTEGER      NOT NULL UNIQUE,
    data        DATE         NOT NULL,
    dezenas     INTEGER[]    NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bets_user_id       ON bets(user_id);
CREATE INDEX IF NOT EXISTS idx_bets_created_at    ON bets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email        ON users(email);
CREATE INDEX IF NOT EXISTS idx_concursos_concurso ON concursos(concurso DESC);
