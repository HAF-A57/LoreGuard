"""
LLM-Based Metadata Extraction Service

Uses LLM providers and prompt templates to intelligently extract metadata
from documents. Falls back to regex-based extraction if LLM unavailable.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMMetadataExtractionService:
    """Service for extracting metadata using LLM providers and prompt templates"""
    
    def __init__(self):
        """Initialize LLM metadata extraction service"""
        # Setup database access for svc-api models
        apps_dir = Path(__file__).resolve().parent.parent.parent.parent
        svc_api_app_path = apps_dir / 'svc-api' / 'app'
        if str(svc_api_app_path) not in sys.path:
            sys.path.insert(0, str(svc_api_app_path))
        
        # Use shared database engine (singleton pattern)
        # Import here to avoid circular imports
        from app.db.database import get_session
        # Store reference to get_session function instead of creating engine
        self.get_session = get_session
    
    async def extract_metadata_llm(
        self,
        text_content: str,
        artifact_uri: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract metadata using LLM and prompt template
        
        Args:
            text_content: Normalized text content of the document
            artifact_uri: URI/URL of the artifact
            processing_options: Optional processing configuration
            
        Returns:
            Dictionary with extracted metadata, or None if LLM extraction fails
        """
        # Use shared database engine via get_session()
        session = self.get_session()
        
        try:
            from models.llm_provider import LLMProvider
            from models.prompt_template import PromptTemplate
            
            # Get active LLM provider
            provider = self._get_provider(session)
            if not provider:
                logger.warning("No active LLM provider found, skipping LLM metadata extraction")
                return None
            
            if provider.status != "active":
                logger.warning(f"LLM provider {provider.name} is not active, skipping LLM metadata extraction")
                return None
            
            # Load metadata extraction prompt template
            template = session.query(PromptTemplate).filter(
                PromptTemplate.type == "metadata",
                PromptTemplate.is_active == True
            ).order_by(PromptTemplate.created_at.desc()).first()
            
            if not template:
                logger.warning("No active metadata extraction prompt template found, skipping LLM extraction")
                return None
            
            logger.info(f"Using LLM metadata extraction with template: {template.reference_id}")
            
            # Prepare content preview (first 10000 characters as per template)
            content_preview = text_content[:10000]
            
            # Build prompts from template
            system_prompt = template.system_prompt or ""
            user_prompt = template.user_prompt_template.format(
                artifact_uri=artifact_uri,
                document_content_preview=content_preview
            )
            
            # Call LLM based on provider type
            if provider.provider in ["openai", "azure"]:
                result = await self._extract_openai(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=provider.model
                )
            elif provider.provider == "anthropic":
                result = await self._extract_anthropic(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=provider.model
                )
            else:
                logger.warning(f"Unsupported LLM provider type: {provider.provider}")
                return None
            
            # Increment template usage count
            self._increment_template_usage(session, template.reference_id)
            
            logger.info(f"LLM metadata extraction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"LLM metadata extraction failed: {e}", exc_info=True)
            return None
        finally:
            session.close()
    
    async def _extract_openai(
        self,
        provider,
        system_prompt: str,
        user_prompt: str,
        model: str
    ) -> Dict[str, Any]:
        """Extract metadata using OpenAI/Azure OpenAI API"""
        base_url = provider.base_url or "https://api.openai.com/v1"
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        if base_url.endswith("/"):
            base_url = base_url.rstrip("/")
        
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use tools API with strict mode for structured output
        tool_schema = {
            "type": "function",
            "function": {
                "name": "extract_metadata",
                "description": "Extract structured metadata from document",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": ["string", "null"],
                            "description": "Document title (exact as published, exclude boilerplate)"
                        },
                        "authors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of full author names with credentials if available"
                        },
                        "organization": {
                            "type": ["string", "null"],
                            "description": "Publishing institution, think tank, university, agency"
                        },
                        "publication_date": {
                            "type": ["string", "null"],
                            "description": "Publication date in YYYY-MM-DD, YYYY-MM, or YYYY format"
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of 3-10 specific topic keywords relevant to wargaming"
                        },
                        "geo_location": {
                            "type": ["string", "null"],
                            "description": "Primary countries, regions, or theaters discussed"
                        },
                        "language": {
                            "type": "string",
                            "description": "ISO 639-1 language code (default: en)"
                        },
                        "document_type": {
                            "type": "string",
                            "enum": ["academic", "think_tank", "government", "media", "technical", "other"],
                            "description": "Document type classification"
                        },
                        "venue_type": {
                            "type": ["string", "null"],
                            "description": "Venue characteristics (e.g., peer-reviewed journal, policy brief)"
                        },
                        "classification": {
                            "type": ["string", "null"],
                            "description": "Classification markings or distribution restrictions if explicitly stated"
                        }
                    },
                    "required": ["title", "authors", "organization", "publication_date", "topics", "geo_location", "language", "document_type"],
                    "additionalProperties": False
                }
            }
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "tools": [tool_schema],
            "tool_choice": {"type": "function", "function": {"name": "extract_metadata"}},
            "temperature": float(provider.temperature) if provider.temperature else 0.1
        }
        
        async with httpx.AsyncClient(timeout=float(provider.timeout) if provider.timeout else 30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract tool call arguments
            message = result["choices"][0]["message"]
            
            try:
                if "tool_calls" in message and message["tool_calls"]:
                    tool_call = message["tool_calls"][0]
                    arguments_str = tool_call["function"]["arguments"]
                    # Handle both string and dict arguments
                    if isinstance(arguments_str, dict):
                        metadata = arguments_str
                    else:
                        metadata = json.loads(arguments_str)
                elif "function_call" in message:
                    arguments_str = message["function_call"]["arguments"]
                    if isinstance(arguments_str, dict):
                        metadata = arguments_str
                    else:
                        metadata = json.loads(arguments_str)
                else:
                    # Try to parse content as JSON
                    content = message.get("content", "")
                    try:
                        metadata = json.loads(content)
                    except json.JSONDecodeError:
                        # Try to extract JSON from text
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            metadata = json.loads(json_match.group())
                        else:
                            raise RuntimeError(f"Could not parse OpenAI response as JSON: {content[:200]}")
                
                # Validate metadata structure
                if not isinstance(metadata, dict):
                    raise ValueError(f"Expected dict but got {type(metadata)}: {metadata}")
                
                # Normalize keys (remove whitespace, handle formatting issues)
                normalized_metadata = {}
                for key, value in metadata.items():
                    # Clean up key (remove newlines, extra spaces, quotes)
                    clean_key = key.strip().strip('"\'')
                    normalized_metadata[clean_key] = value
                
                return normalized_metadata
                
            except (KeyError, json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing OpenAI response: {e}")
                logger.debug(f"Response message: {message}")
                raise RuntimeError(f"Failed to parse OpenAI metadata response: {e}") from e
    
    async def _extract_anthropic(
        self,
        provider,
        system_prompt: str,
        user_prompt: str,
        model: str
    ) -> Dict[str, Any]:
        """Extract metadata using Anthropic Claude API"""
        base_url = provider.base_url or "https://api.anthropic.com/v1"
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        if base_url.endswith("/"):
            base_url = base_url.rstrip("/")
        
        url = f"{base_url}/messages"
        headers = {
            "x-api-key": provider.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": int(provider.max_tokens) if provider.max_tokens else 2500,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        
        async with httpx.AsyncClient(timeout=float(provider.timeout) if provider.timeout else 30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract text content
            content = ""
            if "content" in result and len(result["content"]) > 0:
                content = result["content"][0].get("text", "")
            
            # Parse JSON from response
            try:
                metadata = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from text if it's embedded
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    metadata = json.loads(json_match.group())
                else:
                    raise RuntimeError(f"Could not parse Anthropic response as JSON: {content[:200]}")
            
            # Validate metadata structure
            if not isinstance(metadata, dict):
                raise ValueError(f"Expected dict but got {type(metadata)}: {metadata}")
            
            # Normalize keys (remove whitespace, handle formatting issues)
            normalized_metadata = {}
            for key, value in metadata.items():
                # Clean up key (remove newlines, extra spaces, quotes)
                clean_key = key.strip().strip('"\'')
                normalized_metadata[clean_key] = value
            
            return normalized_metadata
    
    def _get_provider(self, session) -> Optional[Any]:
        """Get active LLM provider"""
        from models.llm_provider import LLMProvider
        
        # Try default provider first
        provider = session.query(LLMProvider).filter(
            LLMProvider.is_default == True,
            LLMProvider.status == "active"
        ).first()
        
        if provider:
            return provider
        
        # Fall back to any active provider
        return session.query(LLMProvider).filter(
            LLMProvider.status == "active"
        ).first()
    
    def _increment_template_usage(self, session, reference_id: str):
        """Increment usage count for a prompt template"""
        try:
            from models.prompt_template import PromptTemplate
            
            template = session.query(PromptTemplate).filter(
                PromptTemplate.reference_id == reference_id
            ).first()
            
            if template:
                current_count = int(template.usage_count) if template.usage_count else 0
                template.usage_count = str(current_count + 1)
                session.commit()
        except Exception as e:
            logger.warning(f"Failed to increment template usage count: {e}")
            session.rollback()

