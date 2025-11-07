"""
Chat Session Management Service

Manages chat sessions, messages, context windows, and conversation history.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.chat import ChatSession, ChatMessage
from app.core.config import settings
from app.services.llm_client import LLMClient
from app.services.context_service import ContextRetrievalService
from app.services.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class ChatSessionManager:
    """Manages chat sessions and conversation flow"""
    
    def __init__(self, db: Session, llm_client: LLMClient):
        self.db = db
        self.llm_client = llm_client
        self.context_service = ContextRetrievalService(db)
        self.tool_executor = ToolExecutor(db)
    
    def create_session(self, user_id: str, title: Optional[str] = None) -> ChatSession:
        """
        Create a new chat session
        
        Args:
            user_id: User identifier
            title: Optional session title
            
        Returns:
            New ChatSession instance
        """
        session = ChatSession(
            user_id=user_id,
            title=title or "New Conversation",
            total_tokens=0,
            message_count=0,
            is_active=True
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created new chat session {session.id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """
        Get a chat session
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            ChatSession or None
        """
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
    
    def list_user_sessions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = False
    ) -> Tuple[List[ChatSession], int]:
        """
        List user's chat sessions
        
        Args:
            user_id: User identifier
            skip: Number to skip
            limit: Maximum to return
            active_only: Only return active sessions
            
        Returns:
            Tuple of (sessions, total_count)
        """
        query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)
        
        if active_only:
            query = query.filter(ChatSession.is_active == True)
        
        total = query.count()
        sessions = query.order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
        
        return sessions, total
    
    def add_message(
        self,
        session: ChatSession,
        role: str,
        content: str,
        token_count: Optional[int] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_results: Optional[List[Dict[str, Any]]] = None,
        model_used: Optional[str] = None
    ) -> ChatMessage:
        """
        Add a message to a session
        
        Args:
            session: ChatSession instance
            role: Message role (user, assistant, system, tool)
            content: Message content
            token_count: Optional token count
            tool_calls: Optional tool calls
            tool_call_results: Optional tool call results
            model_used: Optional model identifier
            
        Returns:
            New ChatMessage instance
        """
        # Count tokens if not provided
        if token_count is None:
            token_count = self.llm_client.count_tokens(content)
        
        message = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            token_count=token_count,
            tool_calls=tool_calls,
            tool_call_results=tool_call_results,
            model_used=model_used
        )
        
        self.db.add(message)
        
        # Update session
        session.add_message_tokens(token_count)
        session.update_activity()
        
        # Auto-generate title from first user message
        if session.message_count == 1 and role == "user" and (not session.title or session.title == "New Conversation"):
            session.title = self._generate_title_from_message(content)
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def _generate_title_from_message(self, content: str) -> str:
        """Generate a session title from first message"""
        # Take first 50 chars and clean up
        title = content[:50].strip()
        if len(content) > 50:
            title += "..."
        return title
    
    def get_conversation_messages(
        self,
        session: ChatSession,
        include_system: bool = True,
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation messages for LLM
        
        Manages context window by truncating or summarizing old messages.
        
        Args:
            session: ChatSession instance
            include_system: Include system messages
            max_tokens: Maximum tokens (default from settings)
            
        Returns:
            List of messages in LLM format
        """
        max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS
        
        # Get all messages
        all_messages = session.messages
        
        # Convert to LLM format
        messages = []
        total_tokens = 0
        
        # Add system message with context if requested
        if include_system:
            system_content = self._build_system_message(session.user_id)
            system_tokens = self.llm_client.count_tokens(system_content)
            
            messages.append({
                "role": "system",
                "content": system_content
            })
            total_tokens += system_tokens
        
        # Add context summary if available
        if session.context_summary:
            summary_tokens = self.llm_client.count_tokens(session.context_summary)
            if total_tokens + summary_tokens < max_tokens:
                messages.append({
                    "role": "system",
                    "content": f"Previous conversation summary:\n{session.context_summary}"
                })
                total_tokens += summary_tokens
        
        # Add messages from newest to oldest until we hit token limit
        # We want to keep recent messages and truncate old ones
        included_messages = []
        
        for msg in reversed(all_messages):
            if not msg.is_included_in_context:
                continue
            
            msg_dict = msg.to_llm_format()
            msg_tokens = msg.token_count or self.llm_client.count_tokens(msg.content)
            
            if total_tokens + msg_tokens > max_tokens:
                # We've hit the limit
                break
            
            included_messages.insert(0, msg_dict)  # Insert at beginning to maintain order
            total_tokens += msg_tokens
        
        messages.extend(included_messages)
        
        logger.info(f"Built conversation context with {len(messages)} messages, {total_tokens} tokens")
        
        return messages
    
    def _build_system_message(self, user_id: str) -> str:
        """Build system message with user context"""
        
        # Get context summary
        context_summary = self.context_service.get_context_summary(user_id)
        
        system_message = f"""You are the LoreGuard AI Assistant, helping users with the LoreGuard Facts & Perspectives Harvesting System for military wargaming operations.

You have access to the user's LoreGuard environment and can:
1. View and explain rubrics, artifacts, sources, jobs, and evaluations
2. Search and analyze artifacts
3. Trigger actions like source crawls and artifact evaluations
4. Provide guidance on system configuration and usage
5. Monitor system health and job status

{context_summary}

Always provide accurate, helpful responses based on the user's actual data. When using tools, explain what you're doing and what you found. Be concise but comprehensive.
"""
        
        return system_message
    
    async def manage_context_window(self, session: ChatSession) -> bool:
        """
        Manage context window by summarizing old messages
        
        Returns True if summarization was performed
        """
        # Check if we need to compress
        threshold_tokens = int(settings.MAX_CONTEXT_TOKENS * settings.CONTEXT_COMPRESSION_THRESHOLD)
        
        if session.total_tokens < threshold_tokens:
            return False
        
        logger.info(f"Context window threshold reached for session {session.id}, compressing...")
        
        # Get messages to summarize (older messages not already summarized)
        messages_to_summarize = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id,
            ChatMessage.is_summarized == False,
            ChatMessage.is_included_in_context == True
        ).order_by(ChatMessage.created_at).limit(
            settings.SUMMARIZATION_INTERVAL
        ).all()
        
        if len(messages_to_summarize) < 5:
            # Not enough messages to summarize
            return False
        
        # Build conversation text from messages
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages_to_summarize
        ])
        
        # Create summarization request
        summarization_prompt = f"""Summarize the following conversation concisely, preserving key information and context:

{conversation_text}

Provide a brief summary (2-3 sentences) of the main points discussed."""
        
        try:
            # Use LLM to summarize
            summary_response = await self.llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes conversations concisely."},
                    {"role": "user", "content": summarization_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            summary = summary_response["content"]
            
            # Update session with summary
            if session.context_summary:
                session.context_summary += f"\n\n{summary}"
            else:
                session.context_summary = summary
            
            # Mark messages as summarized
            for msg in messages_to_summarize:
                msg.is_summarized = True
                msg.is_included_in_context = False  # Don't include in future context
            
            self.db.commit()
            
            logger.info(f"Summarized {len(messages_to_summarize)} messages for session {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return False
    
    async def process_user_message(
        self,
        session: ChatSession,
        user_message: str,
        use_tools: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate assistant response
        
        Args:
            session: ChatSession instance
            user_message: User's message
            use_tools: Enable tool calling
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            Dictionary with user message, assistant message, and metadata
        """
        
        # Add user message to session
        user_msg_obj = self.add_message(
            session=session,
            role="user",
            content=user_message
        )
        
        # Check if we need to manage context window
        await self.manage_context_window(session)
        
        # Get conversation history
        conversation_messages = self.get_conversation_messages(session)
        
        # Get available tools
        tools = self.llm_client.get_available_tools() if use_tools else None
        
        # Generate completion
        try:
            response = await self.llm_client.chat_completion(
                messages=conversation_messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Handle tool calls if present
            tools_used = []
            tool_results = []
            
            if response.get("tool_calls"):
                logger.info(f"Assistant requested {len(response['tool_calls'])} tool calls")
                
                for tool_call in response["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    
                    # Execute tool
                    result = await self.tool_executor.execute_tool(function_name, arguments)
                    
                    tools_used.append(function_name)
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "function_name": function_name,
                        "result": result
                    })
                
                # If tools were called, store the assistant message with tool calls
                tool_call_msg = self.add_message(
                    session=session,
                    role="assistant",
                    content=response.get("content", "") or "",
                    tool_calls=response["tool_calls"],
                    model_used=response.get("model")
                )
                
                # Store tool result messages in database
                for tool_result in tool_results:
                    tool_msg = ChatMessage(
                        session_id=session.id,
                        role="tool",
                        content=json.dumps(tool_result["result"]),
                        tool_call_results=[tool_result],
                        message_metadata={"tool_call_id": tool_result["tool_call_id"]}
                    )
                    self.db.add(tool_msg)
                
                self.db.commit()  # Commit all messages
                
                # Now build messages for second completion
                # Get ALL messages including the ones we just added
                conversation_with_tools = self.get_conversation_messages(session, include_system=True, max_tokens=settings.MAX_CONTEXT_TOKENS)
                
                # Make final completion with tool results
                final_response = await self.llm_client.chat_completion(
                    messages=conversation_with_tools,  # Use the manually constructed messages with tool results
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Add final assistant message
                assistant_msg = self.add_message(
                    session=session,
                    role="assistant",
                    content=final_response["content"],
                    model_used=final_response.get("model")
                )
                
                # Combine usage stats
                total_usage = {
                    "prompt_tokens": response["usage"]["prompt_tokens"] + final_response["usage"]["prompt_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"] + final_response["usage"]["completion_tokens"],
                    "total_tokens": response["usage"]["total_tokens"] + final_response["usage"]["total_tokens"]
                }
                
            else:
                # No tool calls, just add assistant message
                assistant_msg = self.add_message(
                    session=session,
                    role="assistant",
                    content=response["content"],
                    model_used=response.get("model")
                )
                
                total_usage = response["usage"]
                tools_used = []
            
            return {
                "user_message": user_msg_obj,
                "assistant_message": assistant_msg,
                "usage": total_usage,
                "tools_used": tools_used,
                "session_tokens": session.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            
            # Add error message
            error_msg = self.add_message(
                session=session,
                role="assistant",
                content=f"I apologize, but I encountered an error processing your request: {str(e)}"
            )
            
            return {
                "user_message": user_msg_obj,
                "assistant_message": error_msg,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "tools_used": [],
                "error": str(e)
            }
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete a chat session
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted
        """
        session = self.get_session(session_id, user_id)
        
        if not session:
            return False
        
        self.db.delete(session)
        self.db.commit()
        
        logger.info(f"Deleted chat session {session_id}")
        return True
    
    def archive_session(self, session_id: str, user_id: str) -> bool:
        """
        Archive a chat session (mark as inactive)
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            True if archived
        """
        session = self.get_session(session_id, user_id)
        
        if not session:
            return False
        
        session.is_active = False
        self.db.commit()
        
        logger.info(f"Archived chat session {session_id}")
        return True
    
    def get_session_with_messages(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """
        Get session with all messages loaded
        
        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            
        Returns:
            ChatSession with messages relationship loaded
        """
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if session:
            # Ensure messages are loaded
            _ = session.messages
        
        return session
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.tool_executor.cleanup()

