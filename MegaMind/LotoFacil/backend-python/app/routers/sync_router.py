"""Sync router — endpoints for importing lottery results, dashboard stats, and last update info."""

from fastapi import APIRouter

from app.services.sync_service import SyncService

router = APIRouter()

sync_service = SyncService()


@router.post("/sync-results")
async def sync_results():
    """
    Fetch the latest 100 Lotofácil results from the Caixa API
    and upsert them into the database. Auto-triggers cache update.
    """
    result = await sync_service.sync_results(count=100)
    return result


@router.get("/sync-results/stats")
async def get_stats():
    """Return dashboard statistics (contests count, bets count, etc)."""
    return await sync_service.get_stats()


@router.get("/last-update")
async def get_last_update():
    """
    Return the timestamp of the last automatic update.
    Used by the frontend to show "Atualizado em: ..." badge
    and trigger silent refresh when timestamp changes.
    """
    return await sync_service.get_last_update()
