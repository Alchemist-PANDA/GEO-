import json
try:
    import redis.asyncio as aioredis
    REDIS_ASYNC_AVAILABLE = True
except ImportError:
    REDIS_ASYNC_AVAILABLE = False

if not REDIS_ASYNC_AVAILABLE:
    class MockAioRedis:
        @classmethod
        def from_url(cls, *args, **kwargs):
            class MockPubSub:
                async def subscribe(self, *args, **kwargs):
                    pass
                async def unsubscribe(self, *args, **kwargs):
                    pass
                async def listen(self):
                    # Yield nothing
                    if False:
                        yield None
            class MockClient:
                def pubsub(self):
                    return MockPubSub()
                async def aclose(self):
                    pass
            return MockClient()
    aioredis = MockAioRedis()  # type: ignore

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from geo_audit_agent.api.auth import get_current_user

router = APIRouter()


async def audit_event_stream(audit_id: str, user_id: str):
    import os
    import logging
    redis_url = None
    try:
        import streamlit as st
        redis_url = st.secrets.get("redis_url")
    except Exception:
        pass
    if not redis_url:
        redis_url = os.getenv("REDIS_URL")

    from typing import Any
    r: Any = None
    if REDIS_ASYNC_AVAILABLE and redis_url:
        try:
            r = aioredis.from_url(redis_url)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to connect to Redis at {redis_url}: {e}")
            r = None

    if r is None:
        class MockPubSub:
            async def subscribe(self, *args, **kwargs):
                pass
            async def unsubscribe(self, *args, **kwargs):
                pass
            async def listen(self):
                if False:
                    yield None
        class MockClient:
            def pubsub(self):
                return MockPubSub()
            async def aclose(self):
                pass
        r = MockClient()

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
