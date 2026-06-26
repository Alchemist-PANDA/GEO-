import uuid
import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, desc
from pydantic import BaseModel

from geo_audit_agent.api.auth import get_current_user
from geo_audit_agent.db.session import get_async_session
from geo_audit_agent.db.models import CopilotConversation, CopilotMessage
from geo_audit_agent.copilot.engine import stream_chat

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None  # None = new conversation
    message: str
    context: Dict[str, Any]

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    preview: str

class RenameRequest(BaseModel):
    title: str

@router.post("/copilot/chat")
async def chat_endpoint(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """
    Streaming chat endpoint returning Server-Sent Events (SSE).
    """
    user_uuid = uuid.UUID(user_id)
    conversation_id = request.conversation_id

    # If no conversation ID, create a new one
    if not conversation_id:
        conversation = CopilotConversation(
            user_id=user_uuid,
            title="New conversation",
            context_snapshot=request.context
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        conversation_id = str(conversation.id)
    else:
        # Validate conversation ownership
        conversation = session.get(CopilotConversation, uuid.UUID(conversation_id))
        if not conversation or conversation.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

    async def event_generator():
        try:
            # Yield initial connection confirmation
            yield f"data: {json.dumps({'type': 'init', 'conversation_id': conversation_id})}\n\n"
            
            # Stream the actual chat interaction
            async for event in stream_chat(conversation_id, request.message, request.context, session):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/copilot/history", response_model=List[ConversationSummary])
async def get_history(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """
    Retrieve all conversation summaries belonging to the user.
    """
    user_uuid = uuid.UUID(user_id)
    statement = select(CopilotConversation).where(
        CopilotConversation.user_id == user_uuid
    ).order_by(desc(CopilotConversation.updated_at))
    
    conversations = session.exec(statement).all()
    summaries = []
    
    for conv in conversations:
        # Get preview of last assistant message
        preview = ""
        if conv.messages:
            last_msg = conv.messages[-1]
            preview = last_msg.content[:100]
        
        summaries.append(ConversationSummary(
            id=str(conv.id),
            title=conv.title,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            message_count=len(conv.messages),
            preview=preview
        ))
        
    return summaries

@router.get("/copilot/history/{id}")
async def get_conversation(
    id: str,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """
    Get full details of a single conversation, including messages.
    """
    user_uuid = uuid.UUID(user_id)
    conversation = session.get(CopilotConversation, uuid.UUID(id))
    
    if not conversation or conversation.user_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
        
    messages_data = []
    for msg in conversation.messages:
        messages_data.append({
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "artifacts": msg.artifacts,
            "created_at": msg.created_at.isoformat()
        })
        
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "context_snapshot": conversation.context_snapshot,
        "created_at": conversation.created_at.isoformat(),
        "messages": messages_data
    }

@router.delete("/copilot/history/{id}")
async def delete_conversation(
    id: str,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """
    Delete a single conversation.
    """
    user_uuid = uuid.UUID(user_id)
    conversation = session.get(CopilotConversation, uuid.UUID(id))
    
    if not conversation or conversation.user_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
        
    try:
        session.delete(conversation)
        session.commit()
        return {"status": "success", "message": "Conversation deleted"}
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )

@router.delete("/copilot/history")
async def clear_all_history(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """
    Clear all conversations belonging to the user.
    """
    user_uuid = uuid.UUID(user_id)
    statement = select(CopilotConversation).where(CopilotConversation.user_id == user_uuid)
    conversations = session.exec(statement).all()
    
    try:
        for conv in conversations:
            session.delete(conv)
        session.commit()
        return {"status": "success", "message": "All conversations cleared"}
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to clear history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear history"
        )

@router.patch("/copilot/history/{id}")
async def rename_conversation(
    id: str,
    payload: RenameRequest,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_async_session)
):
    """
    Rename a conversation.
    """
    user_uuid = uuid.UUID(user_id)
    conversation = session.get(CopilotConversation, uuid.UUID(id))
    
    if not conversation or conversation.user_id != user_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
        
    try:
        conversation.title = payload.title
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        session.commit()
        return {"status": "success", "title": conversation.title}
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to rename conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rename conversation"
        )
