"""
Scheduler Service — Automates sync and stats recalculation.

Uses APScheduler to run sync at strategic times:
  - Monday to Saturday at 21:00, 21:30, and 22:00 (Lotofácil draws ~20:00)
  - After each successful sync with new data, triggers stats cache update
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
sync_service = SyncService()


async def scheduled_sync():
    """Job to sync results and update stats cache if new data found."""
    logger.info("[SCHEDULER] ⏰ Starting scheduled sync job...")
    try:
        result = await sync_service.sync_results(count=50)
        inserted = result.get("inserted", 0)
        logger.info("[SCHEDULER] ✅ Sync completed. Inserted: %d", inserted)

        if inserted > 0:
            logger.info("[SCHEDULER] 🔄 New data found! Triggering stats cache update...")
            await sync_service.update_statistics_cache()
            logger.info("[SCHEDULER] ✅ Statistics cache updated successfully.")
        else:
            logger.info("[SCHEDULER] ℹ️ No new contests. Cache unchanged.")

    except Exception as e:
        logger.error("[SCHEDULER] ❌ Sync job failed: %s", e)


def start_scheduler():
    """Initialize and start the scheduler with strategic times."""

    # Lotofácil draws happen Mon-Sat around 20:00
    # Schedule at 21:00, 21:30, 22:00 to catch results as they become available
    times = [
        {"hour": 21, "minute": 0},
        {"hour": 21, "minute": 30},
        {"hour": 22, "minute": 0},
    ]

    for i, t in enumerate(times):
        trigger = CronTrigger(
            day_of_week="mon-sat",
            hour=t["hour"],
            minute=t["minute"],
            timezone="America/Sao_Paulo",
        )
        scheduler.add_job(
            scheduled_sync,
            trigger=trigger,
            id=f"lottery_sync_{i}",
            name=f"Lottery Sync {t['hour']}:{t['minute']:02d}",
            replace_existing=True,
        )
        logger.info(
            "[SCHEDULER] 📅 Job registered: Mon-Sat %d:%02d (America/Sao_Paulo)",
            t["hour"], t["minute"]
        )

    scheduler.start()
    logger.info("[SCHEDULER] ✅ Scheduler started with %d jobs.", len(times))


def shutdown_scheduler():
    """Shutdown the scheduler."""
    scheduler.shutdown()
    logger.info("[SCHEDULER] 🛑 Shutdown complete.")
