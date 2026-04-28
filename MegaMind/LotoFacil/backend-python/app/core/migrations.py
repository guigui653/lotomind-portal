"""
Database migration script to create tables without data loss.
Avoiding full reset (docker-compose down -v).
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

async def run_migrations():
    """Create missing tables."""
    logger.info("Running database migrations...")
    async with engine.begin() as conn:
        # ── Predictions table ──
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lotomind.predictions (
                id SERIAL PRIMARY KEY,
                numbers INTEGER[] NOT NULL,
                concurso_alvo INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                strategy_name VARCHAR(50) DEFAULT 'balanced'
            );
        """))

        # ── Dashboard Stats cache table ──
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lotomind.dashboard_stats (
                key VARCHAR(100) PRIMARY KEY,
                value JSONB NOT NULL DEFAULT '{}',
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

    logger.info("Migrations completed (predictions + dashboard_stats).")

if __name__ == "__main__":
    asyncio.run(run_migrations())
