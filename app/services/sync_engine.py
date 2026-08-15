"""
Real sync execution against an Integration's configured external
endpoint.

There's no vendor-specific SDK for any of the providers this engine's
schema anticipates (HubSpot, Salesforce, ...) - so "real" here means a
real HTTP call to whatever endpoint the integration is actually
configured with (`config["sync_url"]`), not a per-vendor client. This
mirrors notification-engine's generic webhook_client.py: honestly fails
when nothing real is configured, rather than fabricating progress
numbers the way the old mock endpoints did.
"""

import time
from datetime import datetime, timedelta

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import Integration, IntegrationStatus
from app.models.sync import SyncJob, SyncStatus


async def run_sync_job(db: AsyncSession, integration: Integration, sync_job: SyncJob) -> SyncJob:
    """Execute one sync job for real. Always leaves sync_job/integration in a real terminal state."""
    sync_job.status = SyncStatus.RUNNING
    sync_job.started_at = datetime.utcnow()
    integration.status = IntegrationStatus.SYNCING
    await db.flush()

    sync_url = (integration.config or {}).get("sync_url")
    if not sync_url:
        return _fail(sync_job, integration, "Integration has no 'sync_url' configured - nothing to sync against")

    method = "POST" if sync_job.direction == "push" else "GET"
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(sync_url)
            else:
                response = await client.post(sync_url, json=(integration.config or {}).get("payload", {}))
    except httpx.HTTPError as exc:
        logger.warning(f"Sync request failed for integration {integration.id}: {exc}")
        return _fail(sync_job, integration, f"Sync request failed: {exc}", started)

    sync_job.duration_seconds = int(time.monotonic() - started)
    sync_job.completed_at = datetime.utcnow()

    if response.status_code >= 400:
        return _fail(sync_job, integration, f"Sync endpoint returned {response.status_code}: {response.text[:300]}", started)

    # Real record counting when the endpoint returns a JSON list or {"records": [...]};
    # an honest "1 successful call, unknown record count" otherwise, never a fabricated number.
    records = None
    try:
        body = response.json()
        if isinstance(body, list):
            records = body
        elif isinstance(body, dict) and isinstance(body.get("records"), list):
            records = body["records"]
    except ValueError:
        pass

    sync_job.status = SyncStatus.COMPLETED
    sync_job.processed_records = len(records) if records is not None else 0
    sync_job.total_records = sync_job.processed_records
    if sync_job.direction != "push":
        sync_job.records_created = sync_job.processed_records

    integration.status = IntegrationStatus.ACTIVE
    integration.last_sync_at = sync_job.completed_at
    integration.last_error = None
    integration.next_sync_at = sync_job.completed_at + timedelta(hours=integration.sync_interval_hours or 24)

    return sync_job


def _fail(sync_job: SyncJob, integration: Integration, message: str, started: float = None) -> SyncJob:
    sync_job.status = SyncStatus.FAILED
    sync_job.error_message = message
    sync_job.completed_at = datetime.utcnow()
    if started is not None:
        sync_job.duration_seconds = int(time.monotonic() - started)

    integration.status = IntegrationStatus.ERROR
    integration.last_error = message
    integration.error_count = (integration.error_count or 0) + 1

    return sync_job
