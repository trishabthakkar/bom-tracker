import logging

from fastapi import Request

logger = logging.getLogger("app.audit")


def audit_event(
    *,
    event: str,
    request: Request | None = None,
    user_id: int | None = None,
    outcome: str = "success",
    **metadata: object,
) -> None:
    client_host = request.client.host if request and request.client else None
    logger.info(
        "event=%s outcome=%s user_id=%s client=%s metadata=%s",
        event,
        outcome,
        user_id,
        client_host,
        metadata,
    )
