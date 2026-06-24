import json
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from geo_audit_agent.api.auth import get_current_user

router = APIRouter()


async def audit_event_stream(audit_id: str, user_id: str):
    r = aioredis.from_url("redis://localhost:6379/0")
    pubsub = r.pubsub()
    await pubsub.subscribe(f"audit:{audit_id}")

    yield f"event: connected\ndata: {json.dumps({'audit_id': audit_id})}\n\n"

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                yield f"event: {data['event']}\ndata: {json.dumps(data)}\n\n"
                if data.get("event") == "audit_complete":
                    break
    finally:
        await pubsub.unsubscribe(f"audit:{audit_id}")
        await r.aclose()


@router.get("/audits/{audit_id}/stream")
async def stream_audit(
    audit_id: str,
    user_id: str = Depends(get_current_user),
):
    return StreamingResponse(
        audit_event_stream(audit_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
