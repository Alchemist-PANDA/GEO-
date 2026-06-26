"""
Phase 6: Copilot API Tests
Tests for the /v1/copilot/* endpoints using FastAPI TestClient.
Uses an in-memory SQLite database to avoid touching production data.
"""
import uuid
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from geo_audit_agent.db.models import UserProfile, CopilotConversation

# ── Test database (in-memory SQLite) ─────────────────────────────────────────
TEST_DB_URL = "sqlite://"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(test_engine) as session:
        yield session


TEST_USER_ID = str(uuid.uuid4())


def override_get_current_user():
    return TEST_USER_ID


@pytest.fixture(scope="module", autouse=True)
def create_tables():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(scope="module")
def client():
    from geo_audit_agent.api.app import app
    from geo_audit_agent.api.auth import get_current_user
    from geo_audit_agent.db.session import get_async_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_async_session] = override_get_session

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def seed_user():
    from geo_audit_agent.db.models import UserProfile
    user_uuid = uuid.UUID(TEST_USER_ID)
    with Session(test_engine) as session:
        existing = session.get(UserProfile, user_uuid)
        if not existing:
            session.add(UserProfile(
                id=user_uuid,
                email="copilot_test@example.com",
                display_name="Copilot Tester",
                plan_tier="pro",
            ))
            session.commit()


# ── 1. History ────────────────────────────────────────────────────────────────
class TestGetHistory:
    def test_empty_history_returns_list(self, client, seed_user):
        resp = client.get("/v1/copilot/history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_history_contains_created_conv(self, client, seed_user):
        from geo_audit_agent.db.models import CopilotConversation
        conv = CopilotConversation(
            user_id=uuid.UUID(TEST_USER_ID),
            title="History Test Conv",
            context_snapshot={"tab": "GEO Score"},
        )
        with Session(test_engine) as session:
            session.add(conv)
            session.commit()
            session.refresh(conv)
            conv_id = str(conv.id)

        resp = client.get("/v1/copilot/history")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert conv_id in ids

    def test_history_summary_shape(self, client, seed_user):
        resp = client.get("/v1/copilot/history")
        for s in resp.json():
            for key in ("id", "title", "created_at", "updated_at", "message_count", "preview"):
                assert key in s, f"Missing key {key} in summary"


# ── 2. Get single conversation ────────────────────────────────────────────────
class TestGetConversation:
    @pytest.fixture(autouse=True)
    def _create_conv(self, seed_user):
        from geo_audit_agent.db.models import CopilotConversation, CopilotMessage
        with Session(test_engine) as session:
            conv = CopilotConversation(
                user_id=uuid.UUID(TEST_USER_ID),
                title="Detail Test",
                context_snapshot={"tab": "Gap Matrix"},
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            self.conv_id = str(conv.id)

            session.add(CopilotMessage(
                conversation_id=conv.id,
                role="user",
                content="What are my gaps?",
                tokens_used=5,
            ))
            session.commit()

    def test_returns_conversation_with_messages(self, client):
        resp = client.get(f"/v1/copilot/history/{self.conv_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == self.conv_id
        assert data["title"] == "Detail Test"
        assert len(data["messages"]) >= 1
        assert data["messages"][0]["role"] == "user"

    def test_unknown_id_returns_404(self, client):
        resp = client.get(f"/v1/copilot/history/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── 3. Rename conversation ────────────────────────────────────────────────────
class TestRenameConversation:
    @pytest.fixture(autouse=True)
    def _create_conv(self, seed_user):
        from geo_audit_agent.db.models import CopilotConversation
        with Session(test_engine) as session:
            conv = CopilotConversation(
                user_id=uuid.UUID(TEST_USER_ID),
                title="Old Title",
                context_snapshot={},
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            self.conv_id = str(conv.id)

    def test_rename_succeeds(self, client):
        resp = client.patch(
            f"/v1/copilot/history/{self.conv_id}",
            json={"title": "New Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert resp.json()["title"] == "New Title"

    def test_rename_persists(self, client):
        client.patch(f"/v1/copilot/history/{self.conv_id}", json={"title": "Persisted"})
        detail = client.get(f"/v1/copilot/history/{self.conv_id}")
        assert detail.json()["title"] == "Persisted"

    def test_rename_unknown_returns_404(self, client):
        resp = client.patch(
            f"/v1/copilot/history/{uuid.uuid4()}",
            json={"title": "Ghost"},
        )
        assert resp.status_code == 404


# ── 4. Delete single conversation ─────────────────────────────────────────────
class TestDeleteConversation:
    def test_delete_and_gone(self, client, seed_user):
        """Delete a conversation then verify it returns 404.
        Combined into one test to avoid fixture re-creation between methods."""
        from geo_audit_agent.db.models import CopilotConversation
        with Session(test_engine) as session:
            conv = CopilotConversation(
                user_id=uuid.UUID(TEST_USER_ID),
                title="To Be Deleted",
                context_snapshot={},
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            conv_id = str(conv.id)

        # Delete it
        resp = client.delete(f"/v1/copilot/history/{conv_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Confirm it is gone
        resp = client.get(f"/v1/copilot/history/{conv_id}")
        assert resp.status_code == 404

    def test_delete_unknown_returns_404(self, client, seed_user):
        resp = client.delete(f"/v1/copilot/history/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── 5. Clear all history ──────────────────────────────────────────────────────
class TestClearAllHistory:
    def test_clear_all_succeeds(self, client, seed_user):
        from geo_audit_agent.db.models import CopilotConversation
        with Session(test_engine) as session:
            for i in range(2):
                session.add(CopilotConversation(
                    user_id=uuid.UUID(TEST_USER_ID),
                    title=f"Clear Test {i}",
                    context_snapshot={},
                ))
            session.commit()

        resp = client.delete("/v1/copilot/history")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        history = client.get("/v1/copilot/history")
        assert history.json() == []


# ── 6. Chat endpoint ──────────────────────────────────────────────────────────
MOCK_EVENTS = [
    {"type": "text_delta", "content": "Hello "},
    {"type": "text_delta", "content": "from mock!"},
    {"type": "message_stop", "content": "Hello from mock!", "tokens": 5},
]


class TestChatEndpoint:
    @pytest.fixture(autouse=True)
    def _mock_stream(self):
        async def fake_stream(conversation_id, message, context, session):
            for event in MOCK_EVENTS:
                yield event

        with patch(
            "geo_audit_agent.api.routes.copilot.stream_chat",
            side_effect=fake_stream,
        ):
            yield

    def test_new_conversation_stream(self, client, seed_user):
        resp = client.post(
            "/v1/copilot/chat",
            json={
                "message": "What is my GEO score?",
                "context": {"brand_name": "Test Brand", "geo_score": 72},
            },
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        data_lines = [
            line.removeprefix("data:").strip()
            for line in resp.text.split("\n")
            if line.startswith("data:")
        ]
        assert len(data_lines) >= 1

        first = json.loads(data_lines[0])
        assert first["type"] == "init"
        assert "conversation_id" in first

    def test_existing_conversation_stream(self, client, seed_user):
        from geo_audit_agent.db.models import CopilotConversation
        with Session(test_engine) as session:
            conv = CopilotConversation(
                user_id=uuid.UUID(TEST_USER_ID),
                title="Existing",
                context_snapshot={},
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            conv_id = str(conv.id)

        resp = client.post(
            "/v1/copilot/chat",
            json={
                "conversation_id": conv_id,
                "message": "Follow up?",
                "context": {},
            },
        )
        assert resp.status_code == 200

    def test_unknown_conversation_returns_404(self, client, seed_user):
        resp = client.post(
            "/v1/copilot/chat",
            json={
                "conversation_id": str(uuid.uuid4()),
                "message": "Should fail",
                "context": {},
            },
        )
        assert resp.status_code == 404

    def test_missing_message_field_returns_422(self, client, seed_user):
        resp = client.post("/v1/copilot/chat", json={"context": {}})
        assert resp.status_code == 422
