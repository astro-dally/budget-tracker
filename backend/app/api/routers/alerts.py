"""Alert endpoints, including the Server-Sent Events stream."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import StreamingResponse

from app.api import mappers
from app.api.deps import AlertServiceDep, AuthServiceDep, BroadcasterDep
from app.api.schemas import AlertOut, ErrorOut, MarkAllReadOut, UnreadCountOut

router = APIRouter(prefix="/alerts", tags=["alerts"])

KEEP_ALIVE_SECONDS = 15.0


@router.get("", response_model=list[AlertOut], summary="Alert history")
def list_alerts(
    service: AlertServiceDep,
    unread_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AlertOut]:
    """Newest alerts first."""
    return [mappers.alert(alert) for alert in service.list_all(limit, unread_only)]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(service: AlertServiceDep) -> UnreadCountOut:
    """Number of unread alerts for the bell badge."""
    return UnreadCountOut(count=service.unread_count())


@router.post("/read-all", response_model=MarkAllReadOut)
def mark_all_read(service: AlertServiceDep) -> MarkAllReadOut:
    """Mark every alert as read."""
    return MarkAllReadOut(updated=service.mark_all_read())


@router.post(
    "/{alert_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={404: {"model": ErrorOut}},
)
def mark_read(alert_id: str, service: AlertServiceDep) -> Response:
    """Mark one alert as read."""
    service.mark_read(alert_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stream", summary="Live alerts (Server-Sent Events)")
async def stream_alerts(
    request: Request,
    auth: AuthServiceDep,
    broadcaster: BroadcasterDep,
    token: Annotated[str, Query(description="Session token (EventSource can't send headers)")],
) -> StreamingResponse:
    """Push the signed-in user's new alerts as ``alert`` events; keep-alive every 15 s."""
    user = auth.authenticate(token)

    async def events() -> AsyncIterator[str]:
        subscription = broadcaster.subscribe(user.id)
        try:
            yield "retry: 5000\n\n"
            while not await request.is_disconnected():
                alert = await subscription.get(timeout=KEEP_ALIVE_SECONDS)
                if alert is None:
                    yield ": keep-alive\n\n"
                    continue
                payload = mappers.alert(alert).model_dump_json()
                yield f"id: {alert.id}\nevent: alert\ndata: {payload}\n\n"
        finally:
            subscription.close()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
