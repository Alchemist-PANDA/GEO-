import sys
import uuid
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

from geo_audit_agent.copilot.chart_builder import build_chart
from geo_audit_agent.copilot.context import build_copilot_context
from geo_audit_agent.copilot.engine import compact_history
from geo_audit_agent.db.models import CopilotConversation, CopilotMessage, UserProfile

# Setup in-memory sqlite for testing DB
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)

@pytest.fixture(name="db_session")
def db_session_fixture():
    # Create tables
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_db_models(db_session: Session):
    # 1. Create a user profile
    user_id = uuid.uuid4()
    user = UserProfile(
        id=user_id,
        email="test@user.com",
        display_name="Test User",
        plan_tier="free"
    )
    db_session.add(user)
    db_session.commit()

    # 2. Create conversation
    conv = CopilotConversation(
        user_id=user_id,
        title="Test Conversation",
        context_snapshot={"active_tab": "GEO Score"}
    )
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    # 3. Create message
    msg = CopilotMessage(
        conversation_id=conv.id,
        role="user",
        content="Hello Copilot",
        tokens_used=10
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(conv)

    # Asserts
    assert len(conv.messages) == 1
    assert conv.messages[0].content == "Hello Copilot"
    assert conv.messages[0].role == "user"

def test_context_builder():
    session_state = {
        "active_tab": "Gap Matrix",
        "brand_name": "Test Brand",
        "category": "Retail",
        "city": "London",
        "audit_result": {
            "report": {
                "geo_score": 75,
                "citation_rate": 0.8
            },
            "gaps": [{"dimension": "Schema", "severity": "High"}],
            "sentiment": "Positive"
        }
    }
    context = build_copilot_context(session_state)
    assert context["current_tab"] == "Gap Matrix"
    assert context["brand_name"] == "Test Brand"
    assert context["geo_score"] == 75
    assert context["sentiment"] == "Positive"

def test_chart_builder():
    context = {
        "brand_name": "My Brand",
        "geo_score": 80,
        "competitors": [
            {"name": "Comp A", "geo_score": 70},
            {"name": "Comp B", "geo_score": 90}
        ]
    }

    chart_json = build_chart(
        chart_type="bar",
        title="Competitor Comparison",
        data_source="competitor_comparison",
        metrics=[],
        context=context
    )
    assert "Competitor Comparison" in chart_json
    assert "My Brand" in chart_json
    assert "Comp A" in chart_json

def test_compact_history():
    messages = [{"role": "user", "content": "Context"}]
    for i in range(25):
        messages.append({"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"})

    compacted = compact_history(messages)
    assert len(compacted) < 20
    assert compacted[0]["content"] == "Context"
