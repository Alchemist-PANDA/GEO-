# BrandSight GEO AI Copilot — Production-Ready Implementation Plan

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Streamlit Frontend                                             │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ FAB Button │→│ Side Panel   │  │ Dedicated Copilot Page   │ │
│  │ (all pages)│  │ (420px glass)│  │ pages/3_🤖_Copilot.py   │ │
│  └───────────┘  │ Chat + Tools │  │ Full-page chat + history │ │
│                 └──────┬───────┘  └────────────┬─────────────┘ │
│                        │                       │               │
│  ┌─────────────────────┴───────────────────────┘               │
│  │ copilot_state.py — session state manager                    │
│  │ explain_this.py  — "Explain This" button component          │
│  └────────────────────────┬────────────────────────────────────┘│
└───────────────────────────┼────────────────────────────────────-┘
                            │ HTTP (FastAPI)
┌───────────────────────────┼────────────────────────────────────-┐
│  FastAPI Backend          │                                     │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │ POST /v1/copilot/chat         — streaming chat endpoint    │ │
│  │ GET  /v1/copilot/history      — list conversations         │ │
│  │ GET  /v1/copilot/history/{id} — get single conversation    │ │
│  │ DELETE /v1/copilot/history/{id} — delete conversation      │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                     │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │ copilot_engine.py                                          │ │
│  │  - Context assembly (current tab, audit data, brand info)  │ │
│  │  - Claude API streaming (anthropic SDK)                    │ │
│  │  - Tool definitions (chart_gen, data_lookup, navigate)     │ │
│  │  - Conversation compaction for long threads                │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                     │
│  ┌────────────────────────▼───────────────────────────────────┐ │
│  │ PostgreSQL / SQLite                                        │ │
│  │  - copilot_conversations table                             │ │
│  │  - copilot_messages table                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────-┘
```

### Model Selection

| Use Case | Model | Why |
|---|---|---|
| Default Copilot chat | `claude-haiku-4-5` | $1/$5 per MTok — fast responses, cost-efficient for high-volume Q&A |
| Deep analysis / "Explain This" | `claude-haiku-4-5` | Same model, keeps costs predictable; upgrade to `claude-sonnet-4-6` if quality insufficient |
| Chart generation tool calls | `claude-haiku-4-5` | Tool use works identically on all models |

Use the **Anthropic Python SDK** (`anthropic` package) directly — not the existing `llm_client.py` proxy (which uses OpenAI-format `/chat/completions`). The SDK gives native streaming, tool use, and conversation management.

### New Dependency

Add to `requirements.txt`:
```
anthropic>=0.52.0
```

Environment variable: `ANTHROPIC_API_KEY` (the native Anthropic key, not the proxy token).

---

## 2. Database Schema

### New Models in `geo_audit_agent/db/models.py`

```python
class CopilotConversation(SQLModel, table=True):
    __tablename__ = "copilot_conversations"
    __table_args__ = (
        Index("idx_copilot_conv_user_id", "user_id"),
        Index("idx_copilot_conv_created_at", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user_profiles.id", index=True)
    title: str = Field(max_length=200, default="New conversation")
    # Snapshot of what the user was looking at when conversation started
    context_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    messages: List["CopilotMessage"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "CopilotMessage.created_at"}
    )


class CopilotMessage(SQLModel, table=True):
    __tablename__ = "copilot_messages"
    __table_args__ = (
        Index("idx_copilot_msg_conv_id", "conversation_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="copilot_conversations.id", index=True)
    role: str = Field(max_length=20)  # "user" | "assistant"
    content: str  # Plain text or markdown
    # For assistant messages that include generated charts
    artifacts: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=SAColumn(JSONB, server_default=text("'{}'"))
    )
    # Token usage for cost tracking
    tokens_used: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=SAColumn(DateTime(timezone=True), server_default=text("now()"))
    )

    conversation: CopilotConversation = Relationship(back_populates="messages")
```

### Alembic Migration

Create `alembic/versions/xxxx_add_copilot_tables.py`:
- Creates `copilot_conversations` and `copilot_messages` tables
- Adds indexes on `user_id`, `created_at`, `conversation_id`

---

## 3. Backend Implementation

### 3A. Copilot Engine — `geo_audit_agent/copilot/engine.py`

This is the core brain. It handles context assembly, Claude API calls, and tool execution.

```python
# geo_audit_agent/copilot/engine.py

import anthropic
from typing import AsyncIterator

SYSTEM_PROMPT = """You are BrandSight Copilot, an AI assistant for Generative Engine Optimization (GEO).
You help users understand their brand's visibility across AI platforms (ChatGPT, Perplexity, Gemini, etc.).

You have access to the user's current audit data, competitor scans, and GEO scores.
When answering questions:
- Be specific with numbers from their actual data
- Suggest concrete actions with effort/impact estimates (Low/Medium/High)
- Reference specific metrics: GEO Score, Citation Rate, Content Depth, Schema Coverage, Platform Presence
- When asked to visualize data, use the generate_chart tool
- When a user asks about something on a different tab, use the suggest_navigation tool

Current context will be provided in each message."""

TOOLS = [
    {
        "name": "generate_chart",
        "description": "Generate a Plotly chart from audit/competitor data. Use when the user asks for a visualization, comparison chart, trend graph, or any visual representation of data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "radar", "line", "pie", "scatter", "heatmap"],
                    "description": "The type of Plotly chart to generate"
                },
                "title": {"type": "string", "description": "Chart title"},
                "data_source": {
                    "type": "string",
                    "enum": ["audit_scores", "competitor_comparison", "gap_analysis", "platform_breakdown", "trend"],
                    "description": "Which data set to pull from"
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Which metrics to include"
                }
            },
            "required": ["chart_type", "title", "data_source"]
        }
    },
    {
        "name": "suggest_navigation",
        "description": "Suggest the user navigate to a different tab for relevant information. Use when the answer involves data on another tab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tab_name": {
                    "type": "string",
                    "enum": ["GEO Score", "Gap Matrix", "Remediation Plan", "Lift Simulator", "Live Ticker", "Competitor Intelligence", "Brand Visibility"],
                    "description": "Which tab to suggest"
                },
                "reason": {"type": "string", "description": "Why this tab is relevant"}
            },
            "required": ["tab_name", "reason"]
        }
    },
    {
        "name": "lookup_data",
        "description": "Look up specific data points from the current audit. Use to fetch exact numbers before answering.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["brand_scores", "competitor_scores", "gaps", "remediations", "platform_breakdown"],
                    "description": "What data to retrieve"
                }
            },
            "required": ["query_type"]
        }
    }
]
```

**Key functions in engine.py:**

| Function | Purpose |
|---|---|
| `build_context_message(session_state)` | Assembles current tab, audit data, competitor data, brand info into a context string injected as the first user message |
| `stream_chat(conversation_id, user_message, context, db_session)` | Streams Claude response via `client.messages.stream()`, handles tool use loop, yields text chunks and artifact events |
| `execute_tool(tool_name, tool_input, context)` | Dispatches tool calls — `generate_chart` returns Plotly JSON, `suggest_navigation` returns tab info, `lookup_data` returns formatted data |
| `generate_plotly_chart(chart_type, title, data_source, metrics, context)` | Builds a Plotly figure from audit/competitor data, returns `fig.to_json()` |
| `auto_title(messages)` | After 2+ exchanges, calls Claude to generate a 5-word conversation title |
| `compact_history(messages)` | When message count > 20, summarize older messages to stay within context limits |

**Streaming flow:**

```python
async def stream_chat(conversation_id, user_message, context, db_session):
    messages = load_conversation_messages(conversation_id, db_session)
    messages.append({"role": "user", "content": build_context_message(context) + "\n\n" + user_message})

    client = anthropic.Anthropic()

    while True:  # Tool use loop
        with client.messages.stream(
            model="claude-haiku-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            response_text = ""
            tool_uses = []
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    response_text += event.delta.text
                    yield {"type": "text", "content": event.delta.text}
            final_message = stream.get_final_message()

        # Check for tool use
        tool_blocks = [b for b in final_message.content if b.type == "tool_use"]
        if not tool_blocks:
            break

        # Execute tools and continue
        messages.append({"role": "assistant", "content": final_message.content})
        for tool_block in tool_blocks:
            result = execute_tool(tool_block.name, tool_block.input, context)
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": str(result)}]
            })
            if tool_block.name == "generate_chart":
                yield {"type": "chart", "content": result}
            elif tool_block.name == "suggest_navigation":
                yield {"type": "navigation", "content": result}

    # Save to DB
    save_message(conversation_id, "user", user_message, db_session)
    save_message(conversation_id, "assistant", response_text, db_session, artifacts=collected_artifacts)
```

### 3B. API Routes — `geo_audit_agent/api/routes/copilot.py`

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None  # None = new conversation
    message: str
    context: dict  # Current tab, audit data snapshot

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    preview: str  # First 100 chars of last message

# Endpoints:
# POST /v1/copilot/chat          → StreamingResponse (SSE: text chunks + chart artifacts)
# GET  /v1/copilot/history       → List[ConversationSummary] (paginated, newest first)
# GET  /v1/copilot/history/{id}  → Full conversation with all messages
# DELETE /v1/copilot/history/{id} → Delete single conversation
# DELETE /v1/copilot/history      → Clear all conversations for user
# PATCH /v1/copilot/history/{id}  → Rename conversation
```

**SSE format for streaming:**
```
data: {"type": "text", "content": "Based on your "}
data: {"type": "text", "content": "GEO Score of 72, "}
data: {"type": "chart", "content": {"plotly_json": "..."}}
data: {"type": "navigation", "content": {"tab": "Gap Matrix", "reason": "..."}}
data: {"type": "done", "conversation_id": "uuid", "title": "Brand visibility analysis"}
```

### 3C. Register in App — `geo_audit_agent/api/app.py`

Add:
```python
from geo_audit_agent.api.routes import copilot
app.include_router(copilot.router, prefix="/v1", tags=["Copilot"])
```

---

## 4. Frontend Implementation

### 4A. New Files to Create

| File | Purpose |
|---|---|
| `geo_audit_agent/copilot/__init__.py` | Package init |
| `geo_audit_agent/copilot/engine.py` | Core Copilot engine (Section 3A) |
| `geo_audit_agent/copilot/chart_builder.py` | Plotly chart generation from tool calls |
| `geo_audit_agent/copilot/context.py` | Context assembly utilities |
| `geo_audit_agent/ui/copilot_panel.py` | Side panel chat UI component |
| `geo_audit_agent/ui/copilot_fab.py` | Floating Action Button component |
| `geo_audit_agent/ui/explain_this.py` | "Explain This" button component |
| `geo_audit_agent/ui/copilot_history.py` | Conversation history list UI |
| `pages/3_🤖_Copilot.py` | Dedicated full-page Copilot experience |
| `geo_audit_agent/api/routes/copilot.py` | API routes (Section 3B) |

### 4B. Floating Action Button — `geo_audit_agent/ui/copilot_fab.py`

Renders on every page via injection in the main app layout. CSS-only implementation using Streamlit's `st.markdown()` with `unsafe_allow_html=True`.

```python
def render_copilot_fab():
    """Render the floating Copilot button (bottom-right corner)."""
    st.markdown("""
    <style>
    .copilot-fab {
        position: fixed;
        bottom: 32px;
        right: 32px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 8px 32px rgba(124, 58, 237, 0.35);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        animation: fabPulse 3s ease-in-out infinite;
    }
    .copilot-fab:hover {
        transform: scale(1.1);
        box-shadow: 0 12px 40px rgba(124, 58, 237, 0.5);
    }
    @keyframes fabPulse {
        0%, 100% { box-shadow: 0 8px 32px rgba(124, 58, 237, 0.35); }
        50% { box-shadow: 0 8px 32px rgba(124, 58, 237, 0.55); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Use st.button with custom CSS class for the actual click handler
    col1, col2 = st.columns([20, 1])
    with col2:
        if st.button("🤖", key="copilot_fab", help="Open AI Copilot"):
            st.session_state["copilot_open"] = not st.session_state.get("copilot_open", False)
            st.rerun()
```

**Implementation note:** Since Streamlit doesn't natively support fixed-position interactive elements, the FAB uses a combination of CSS positioning for the visual element and a Streamlit button for the click handler. An alternative is `streamlit-float` package for true floating elements.

### 4C. Side Panel — `geo_audit_agent/ui/copilot_panel.py`

Uses `st.sidebar` or a custom CSS panel. The panel renders when `st.session_state["copilot_open"]` is True.

```python
def render_copilot_panel():
    """Render the 420px glassmorphism side panel with chat interface."""
    if not st.session_state.get("copilot_open", False):
        return

    # Panel CSS
    st.markdown("""
    <style>
    .copilot-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 420px;
        height: 100vh;
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border-left: 1px solid rgba(124, 58, 237, 0.1);
        box-shadow: -8px 0 40px rgba(0, 0, 0, 0.08);
        z-index: 9998;
        display: flex;
        flex-direction: column;
        animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
    }
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .copilot-header {
        padding: 20px 24px;
        border-bottom: 1px solid rgba(124, 58, 237, 0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .copilot-header h3 {
        background: linear-gradient(135deg, #7C3AED, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin: 0;
        font-size: 18px;
    }
    .copilot-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px 24px;
    }
    .copilot-input {
        padding: 16px 24px;
        border-top: 1px solid rgba(124, 58, 237, 0.08);
    }
    .msg-user {
        background: linear-gradient(135deg, #7C3AED, #3B82F6);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 85%;
        margin-left: auto;
        font-size: 14px;
        line-height: 1.5;
    }
    .msg-assistant {
        background: rgba(124, 58, 237, 0.06);
        color: #1E293B;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 14px;
        line-height: 1.5;
    }
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
    }
    .typing-indicator span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #7C3AED;
        animation: typingBounce 1.4s ease-in-out infinite;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-8px); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Streamlit layout for the panel (using sidebar or columns)
    with st.container():
        # Header with close button
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown("### 🤖 AI Copilot")
        with c2:
            if st.button("✕", key="close_copilot"):
                st.session_state["copilot_open"] = False
                st.rerun()

        # Messages display
        messages = st.session_state.get("copilot_messages", [])
        for msg in messages:
            css_class = "msg-user" if msg["role"] == "user" else "msg-assistant"
            st.markdown(f'<div class="{css_class}">{msg["content"]}</div>', unsafe_allow_html=True)

            # Render charts inline
            if msg.get("charts"):
                for chart_json in msg["charts"]:
                    fig = plotly.io.from_json(chart_json)
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{msg['id']}")

            # Render navigation suggestions
            if msg.get("navigation"):
                nav = msg["navigation"]
                st.info(f"💡 Check the **{nav['tab']}** tab — {nav['reason']}")

        # Input
        user_input = st.chat_input("Ask about your brand...", key="copilot_input")
        if user_input:
            handle_copilot_message(user_input)
```

**Streamlit implementation approach:** Since Streamlit doesn't support true fixed-position panels with real-time streaming easily, the recommended approach is:

1. **Option A (Recommended): Use `st.sidebar`** — Override sidebar CSS to match the glassmorphism design. This is the most Streamlit-native approach and handles scroll, state, and reruns correctly.

2. **Option B: Use `streamlit-float` + `streamlit-extras`** — Third-party components that enable floating containers. More complex but allows the exact 420px right-panel design.

3. **Option C: Dedicated page only** — Skip the side panel, put everything in `pages/3_🤖_Copilot.py`. Simplest to implement, most reliable.

**Recommendation: Start with Option A (sidebar) + Option C (dedicated page). Add the floating panel as a polish iteration if needed.**

### 4D. "Explain This" Button — `geo_audit_agent/ui/explain_this.py`

A reusable component placed next to every chart, metric, and table.

```python
def explain_this(element_type: str, element_id: str, context_data: dict):
    """
    Render an 'Explain This' button next to a chart/metric/table.

    Args:
        element_type: "chart" | "metric" | "table" | "score"
        element_id: Unique identifier (e.g., "geo_score", "radar_chart", "gap_matrix")
        context_data: The data behind this element (scores, values, etc.)
    """
    button_key = f"explain_{element_type}_{element_id}"

    st.markdown(f"""
    <style>
    .explain-btn {{
        background: rgba(124, 58, 237, 0.08);
        border: 1px solid rgba(124, 58, 237, 0.15);
        border-radius: 8px;
        padding: 4px 12px;
        color: #7C3AED;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    .explain-btn:hover {{
        background: rgba(124, 58, 237, 0.15);
        transform: translateY(-1px);
    }}
    </style>
    """, unsafe_allow_html=True)

    if st.button(f"💡 Explain This", key=button_key):
        prompt = f"Explain this {element_type} to me in simple terms. Here's the data: {json.dumps(context_data)}"
        st.session_state["copilot_open"] = True
        st.session_state["copilot_pending_message"] = prompt
        st.rerun()
```

**Integration points** — Add `explain_this()` calls in:

| File | Where | element_id |
|---|---|---|
| `pages/1_📈_Audit_Tool.py` | After GEO Score metric | `"geo_score"` |
| `pages/1_📈_Audit_Tool.py` | After each tab's main chart | `"gap_matrix"`, `"radar_chart"`, etc. |
| `geo_audit_agent/ui/competitor_intelligence.py` | After radar chart | `"competitor_radar"` |
| `geo_audit_agent/ui/competitor_intelligence.py` | After each competitor card | `"competitor_{name}"` |
| `geo_audit_agent/ui/brand_visibility.py` | After platform breakdown | `"platform_breakdown"` |
| `geo_audit_agent/ui/gap_matrix.py` | After quadrant matrix | `"gap_quadrant"` |
| `geo_audit_agent/ui/remediation_cards.py` | After priority cards | `"remediation_plan"` |
| `geo_audit_agent/ui/lift_simulator.py` | After simulation results | `"lift_simulation"` |

### 4E. Dedicated Copilot Page — `pages/3_🤖_Copilot.py`

Full-page chat experience with conversation history sidebar.

```
┌──────────────────────────────────────────────────────────────┐
│  🤖 AI Copilot                                    [New Chat] │
├──────────────┬───────────────────────────────────────────────┤
│ History      │                                               │
│              │  Welcome! I'm your GEO Copilot.               │
│ Today        │  Ask me anything about your brand's           │
│ ● Brand vis..│  AI visibility.                               │
│ ● GEO score..│                                               │
│              │  ┌─ User ────────────────────────────────────┐ │
│ Yesterday    │  │ How does my GEO score compare to          │ │
│ ● Competitor.│  │ competitors?                              │ │
│              │  └───────────────────────────────────────────┘ │
│ Last 7 Days  │                                               │
│ ● Schema fix.│  ┌─ Copilot ────────────────────────────────┐ │
│ ● Action pl..│  │ Your GEO Score is 72, which ranks #2     │ │
│              │  │ out of 4 in the fast food category...     │ │
│ [Clear All]  │  │                                           │ │
│              │  │ [📊 Competitor Comparison Chart]           │ │
│              │  │                                           │ │
│              │  │ 💡 Tip: Check the Competitor Intel tab    │ │
│              │  │ for detailed breakdowns.                  │ │
│              │  └───────────────────────────────────────────┘ │
│              │                                               │
│              │  ┌──────────────────────────────────[Send]───┐ │
│              │  │ Ask about your brand...                   │ │
│              │  └──────────────────────────────────────────-┘ │
└──────────────┴───────────────────────────────────────────────┘
```

**Layout:** `st.columns([1, 3])` — left column for history, right for chat.

**Chat rendering:** Use `st.chat_message("user")` and `st.chat_message("assistant")` for native Streamlit chat bubbles. Use `st.chat_input()` for the input box.

**Streaming display:** Use `st.write_stream()` or manual `st.empty()` + progressive text updates in a placeholder.

**History sidebar features:**
- Grouped by: Today, Yesterday, Last 7 Days, Older
- Each item shows: truncated title, timestamp
- Click to load/resume conversation
- Hover reveals delete button
- "Clear All" at bottom with confirmation dialog

### 4F. Context Assembly — `geo_audit_agent/copilot/context.py`

```python
def build_copilot_context(session_state: dict) -> dict:
    """
    Assemble context from Streamlit session state for the Copilot.

    Returns a dict injected into the system prompt so Claude knows
    what the user is currently looking at.
    """
    context = {
        "current_tab": session_state.get("active_tab", "unknown"),
        "brand_name": session_state.get("brand_name", ""),
        "category": session_state.get("category", ""),
        "city": session_state.get("city", ""),
    }

    # Audit data (if an audit has been run)
    audit = session_state.get("audit_result")
    if audit:
        context["geo_score"] = audit.get("report", {}).get("geo_score")
        context["citation_rate"] = audit.get("report", {}).get("citation_rate")
        context["gaps"] = audit.get("gaps", [])
        context["remediations"] = audit.get("remediations", {})
        context["sentiment"] = audit.get("sentiment")

    # Competitor data (if a scan has been run)
    competitor = session_state.get("competitor_data")
    if competitor:
        context["brand_scores"] = competitor.get("brand_scores")
        context["competitors"] = [
            {"name": c["scores"]["competitor"], "geo_score": c["scores"]["geo_score"]}
            for c in competitor.get("competitors", [])
        ]
        context["brand_rank"] = competitor.get("summary", {}).get("brand_rank")

    return context
```

### 4G. Chart Builder — `geo_audit_agent/copilot/chart_builder.py`

```python
import plotly.graph_objects as go

def build_chart(chart_type, title, data_source, metrics, context):
    """
    Generate a Plotly figure from a Copilot tool call.

    Returns: plotly figure JSON string
    """
    fig = go.Figure()

    if data_source == "competitor_comparison" and chart_type == "bar":
        competitors = context.get("competitors", [])
        names = [c["name"] for c in competitors]
        scores = [c["geo_score"] for c in competitors]
        fig.add_trace(go.Bar(x=names, y=scores, marker_color="#7C3AED"))

    elif data_source == "audit_scores" and chart_type == "radar":
        categories = ["GEO Score", "Citation Rate", "Content Depth", "Schema", "Platform"]
        # Pull from context...
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself"))

    elif data_source == "gap_analysis" and chart_type == "heatmap":
        # Build from gaps data...
        pass

    # Apply theme
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter", color="#1E293B"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, font=dict(size=16, color="#0F172A")),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig.to_json()
```

---

## 5. CSS Additions to `style.css`

Add these blocks at the end of the existing `style.css`:

```css
/* ============================================
   AI Copilot Styles
   ============================================ */

/* Floating Action Button */
.copilot-fab-container {
    position: fixed;
    bottom: 32px;
    right: 32px;
    z-index: 9999;
}

/* Side Panel */
[data-testid="stSidebar"].copilot-sidebar {
    background: rgba(255, 255, 255, 0.92) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    border-left: 1px solid rgba(124, 58, 237, 0.08) !important;
    box-shadow: -8px 0 40px rgba(0, 0, 0, 0.06) !important;
}

/* Chat Messages */
.copilot-msg-user {
    background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px auto;
    max-width: 85%;
    font-size: 14px;
    line-height: 1.6;
    animation: msgSlideUp 0.3s ease-out;
}

.copilot-msg-assistant {
    background: rgba(124, 58, 237, 0.05);
    border: 1px solid rgba(124, 58, 237, 0.08);
    color: #1E293B;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 0;
    max-width: 85%;
    font-size: 14px;
    line-height: 1.6;
    animation: msgSlideUp 0.3s ease-out;
}

@keyframes msgSlideUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Explain This Button */
.explain-this-btn {
    background: rgba(124, 58, 237, 0.06);
    border: 1px solid rgba(124, 58, 237, 0.12);
    border-radius: 8px;
    padding: 4px 12px;
    color: #7C3AED;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.explain-this-btn:hover {
    background: rgba(124, 58, 237, 0.12);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.15);
}

/* History List */
.copilot-history-item {
    padding: 12px 16px;
    border-radius: 12px;
    margin: 4px 0;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid transparent;
}

.copilot-history-item:hover {
    background: rgba(124, 58, 237, 0.06);
    border-color: rgba(124, 58, 237, 0.1);
}

.copilot-history-item.active {
    background: rgba(124, 58, 237, 0.1);
    border-color: rgba(124, 58, 237, 0.2);
}

/* Typing Indicator */
.copilot-typing {
    display: flex;
    gap: 4px;
    padding: 8px 16px;
}

.copilot-typing span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #7C3AED;
    opacity: 0.6;
    animation: typingBounce 1.4s ease-in-out infinite;
}

.copilot-typing span:nth-child(2) { animation-delay: 0.2s; }
.copilot-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-8px); opacity: 1; }
}

/* Navigation Suggestion Card */
.copilot-nav-suggestion {
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.06), rgba(59, 130, 246, 0.06));
    border: 1px solid rgba(124, 58, 237, 0.12);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 13px;
    color: #1E293B;
}

/* Responsive */
@media (max-width: 768px) {
    .copilot-panel { width: 100% !important; }
    .copilot-msg-user, .copilot-msg-assistant { max-width: 95%; }
}
```

---

## 6. Implementation Order (Phases)

### Phase 1: Foundation (Days 1-2)
| Step | File | Task |
|---|---|---|
| 1.1 | `requirements.txt` | Add `anthropic>=0.52.0` |
| 1.2 | `geo_audit_agent/db/models.py` | Add `CopilotConversation` and `CopilotMessage` models |
| 1.3 | `alembic/versions/xxxx_add_copilot.py` | Create migration |
| 1.4 | `geo_audit_agent/copilot/__init__.py` | Create package |
| 1.5 | `geo_audit_agent/copilot/context.py` | Context assembly |
| 1.6 | `geo_audit_agent/copilot/engine.py` | Core engine with Claude streaming + tools |
| 1.7 | `geo_audit_agent/copilot/chart_builder.py` | Plotly chart generation |

### Phase 2: API Layer (Day 3)
| Step | File | Task |
|---|---|---|
| 2.1 | `geo_audit_agent/api/routes/copilot.py` | Chat + history endpoints |
| 2.2 | `geo_audit_agent/api/routes/__init__.py` | Add copilot import |
| 2.3 | `geo_audit_agent/api/app.py` | Register copilot router |

### Phase 3: Dedicated Copilot Page (Days 4-5)
| Step | File | Task |
|---|---|---|
| 3.1 | `pages/3_🤖_Copilot.py` | Full-page chat with history sidebar |
| 3.2 | `style.css` | Add all Copilot CSS |
| 3.3 | Test streaming, tool use, chart rendering, history CRUD |

### Phase 4: "Explain This" Integration (Day 6)
| Step | File | Task |
|---|---|---|
| 4.1 | `geo_audit_agent/ui/explain_this.py` | Create component |
| 4.2 | `pages/1_📈_Audit_Tool.py` | Add explain buttons to all tabs |
| 4.3 | `geo_audit_agent/ui/competitor_intelligence.py` | Add explain buttons |
| 4.4 | `geo_audit_agent/ui/brand_visibility.py` | Add explain buttons |
| 4.5 | `geo_audit_agent/ui/gap_matrix.py` | Add explain buttons |
| 4.6 | `geo_audit_agent/ui/remediation_cards.py` | Add explain buttons |

### Phase 5: Side Panel + FAB (Days 7-8)
| Step | File | Task |
|---|---|---|
| 5.1 | `geo_audit_agent/ui/copilot_fab.py` | FAB component |
| 5.2 | `geo_audit_agent/ui/copilot_panel.py` | Side panel chat |
| 5.3 | `pages/1_📈_Audit_Tool.py` | Inject FAB + panel |
| 5.4 | Responsive testing, animation polish |

### Phase 6: Tests + Polish (Days 9-10)
| Step | File | Task |
|---|---|---|
| 6.1 | `tests/test_copilot_engine.py` | Unit tests for engine, context, chart builder |
| 6.2 | `tests/test_copilot_api.py` | API endpoint tests |
| 6.3 | `tests/test_copilot_history.py` | History CRUD tests |
| 6.4 | Cost tracking, rate limiting, error handling |

---

## 7. Conversation Management

### Persistent History (Claude Code-style)

- Every conversation is saved to `copilot_conversations` + `copilot_messages` tables
- On page load, fetch conversation list via `GET /v1/copilot/history`
- Conversations are **never auto-deleted** — user must explicitly delete
- History is grouped by time: Today / Yesterday / Last 7 Days / Last 30 Days / Older
- Each conversation shows: auto-generated title, timestamp, preview of last message
- User can rename, delete individual, or "Clear All" (with confirmation)

### Conversation Compaction

When a conversation exceeds 20 messages (~15K tokens), compact older messages:

```python
def compact_history(messages: list) -> list:
    if len(messages) <= 20:
        return messages

    # Keep first 2 messages (system context) and last 10
    old_messages = messages[2:-10]
    summary_prompt = f"Summarize this conversation so far in 3-4 sentences: {format_messages(old_messages)}"

    summary = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": summary_prompt}]
    )

    return [
        messages[0],  # Original context
        {"role": "user", "content": f"[Previous conversation summary: {summary.content[0].text}]"},
        {"role": "assistant", "content": "Understood, I have the context from our previous discussion."},
        *messages[-10:]  # Recent messages
    ]
```

### Auto-titling

After the second user message, auto-generate a title:

```python
def auto_title(first_message: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=20,
        messages=[{"role": "user", "content": f"Generate a 3-5 word title for a conversation that starts with: '{first_message[:200]}'. Return only the title, no quotes."}]
    )
    return response.content[0].text.strip()
```

---

## 8. Cost Estimates

| Operation | Model | Tokens (est.) | Cost |
|---|---|---|---|
| Single chat message | claude-haiku-4-5 | ~2K in / ~500 out | ~$0.0045 |
| "Explain This" click | claude-haiku-4-5 | ~1.5K in / ~300 out | ~$0.003 |
| Chart generation (with tool use) | claude-haiku-4-5 | ~3K in / ~800 out | ~$0.007 |
| Auto-title generation | claude-haiku-4-5 | ~300 in / ~20 out | ~$0.0004 |
| Conversation compaction | claude-haiku-4-5 | ~4K in / ~200 out | ~$0.005 |

**Monthly estimate per active user** (assuming 50 messages/day): ~$7.50/month

To upgrade quality for specific operations, swap `claude-haiku-4-5` for `claude-sonnet-4-6` ($3/$15 per MTok) — roughly 3x the cost but significantly better for complex analysis.

---

## 9. Environment Variables

Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...           # Required: Anthropic API key for Copilot
COPILOT_MODEL=claude-haiku-4-5         # Optional: override default model
COPILOT_MAX_TOKENS=2048                # Optional: max response tokens
COPILOT_RATE_LIMIT=30                  # Optional: messages per hour per user
```

---

## 10. Security Considerations

| Concern | Mitigation |
|---|---|
| Prompt injection via user input | Copilot system prompt includes guardrails; user input is placed in `user` role, never interpolated into system prompt |
| Data leakage across users | All DB queries filter by `user_id` from JWT; conversations are user-scoped |
| Cost runaway | Rate limiting (30 msgs/hour default), max_tokens cap (2048), conversation compaction |
| Auth bypass | Reuse existing `get_current_user()` JWT auth on all copilot endpoints |
| Sensitive data in context | Only inject aggregate scores and metadata into context, never raw PII |

---

## 11. File Tree Summary

```
geo_audit_agent/
├── copilot/
│   ├── __init__.py              # NEW
│   ├── engine.py                # NEW — Core Claude streaming + tool loop
│   ├── context.py               # NEW — Context assembly from session state
│   └── chart_builder.py         # NEW — Plotly chart generation
├── api/routes/
│   ├── copilot.py               # NEW — Chat + history API endpoints
│   └── __init__.py              # MODIFY — Add copilot import
├── ui/
│   ├── copilot_panel.py         # NEW — Side panel chat component
│   ├── copilot_fab.py           # NEW — Floating Action Button
│   ├── copilot_history.py       # NEW — Conversation history list
│   ├── explain_this.py          # NEW — "Explain This" button component
│   ├── competitor_intelligence.py # MODIFY — Add explain buttons
│   ├── brand_visibility.py       # MODIFY — Add explain buttons
│   ├── gap_matrix.py             # MODIFY — Add explain buttons
│   ├── remediation_cards.py      # MODIFY — Add explain buttons
│   └── lift_simulator.py         # MODIFY — Add explain buttons
├── db/
│   └── models.py                # MODIFY — Add CopilotConversation + CopilotMessage
pages/
├── 1_📈_Audit_Tool.py           # MODIFY — Inject FAB + panel + explain buttons
└── 3_🤖_Copilot.py              # NEW — Dedicated Copilot page
style.css                         # MODIFY — Add Copilot CSS
requirements.txt                  # MODIFY — Add anthropic SDK
tests/
├── test_copilot_engine.py       # NEW
├── test_copilot_api.py          # NEW
└── test_copilot_history.py      # NEW

New files: 11
Modified files: 10
```

This plan is ready for implementation. Each phase is independently deployable — Phase 1-3 gives you a working Copilot page, Phase 4 adds "Explain This" everywhere, and Phase 5 adds the premium side panel experience.
