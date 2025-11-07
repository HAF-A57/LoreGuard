"""
LLM Providers API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
import httpx
import logging
import time

from db.database import get_db
from models.llm_provider import LLMProvider
from schemas.llm_provider import (
    LLMProviderResponse,
    LLMProviderListResponse,
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderListItem
)

router = APIRouter()
logger = logging.getLogger(__name__)


def mask_api_key(api_key: str) -> str:
    """Mask API key for display"""
    if not api_key or len(api_key) < 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


async def fetch_openai_models(api_key: str, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch available models from OpenAI API"""
    try:
        # Normalize base_url
        base = base_url or 'https://api.openai.com/v1'
        if not base.startswith('http'):
            base = f'https://{base}'
        if base.endswith('/'):
            base = base.rstrip('/')
        
        url = f"{base}/models"
        logger.debug(f"Fetching OpenAI models from: {url}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            logger.debug(f"OpenAI API response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                # Filter to chat/completion models
                if any(x in model_id for x in ["gpt-4", "gpt-3.5", "gpt-35"]):
                    models.append({
                        "id": model_id,
                        "name": model_id,
                        "provider": "openai",
                        "description": model.get("description", ""),
                        "created": model.get("created")
                    })
            
            logger.info(f"Found {len(models)} OpenAI models")
            return sorted(models, key=lambda x: x.get("created", 0), reverse=True)
            
    except httpx.HTTPStatusError as e:
        error_text = e.response.text[:500] if e.response.text else "No error details"
        logger.error(f"OpenAI API error: {e.response.status_code} - {error_text}")
        
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please check your OpenAI API key."
            )
        elif e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Models endpoint not found. Check your base URL."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch models from OpenAI: {e.response.status_code} - {error_text[:100]}"
            )
    except httpx.TimeoutException:
        logger.error("OpenAI API request timed out")
        raise HTTPException(
            status_code=504,
            detail="Request to OpenAI API timed out. Please try again."
        )
    except Exception as e:
        logger.error(f"Error fetching OpenAI models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models: {str(e)}"
        )


async def fetch_anthropic_models(api_key: str, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch available models from Anthropic API"""
    # Anthropic doesn't have a public models endpoint, so return common models
    common_models = [
        {
            "id": "claude-3-5-sonnet-20241022",
            "name": "Claude 3.5 Sonnet",
            "provider": "anthropic",
            "description": "Latest Claude 3.5 Sonnet model"
        },
        {
            "id": "claude-3-opus-20240229",
            "name": "Claude 3 Opus",
            "provider": "anthropic",
            "description": "Most powerful Claude 3 model"
        },
        {
            "id": "claude-3-sonnet-20240229",
            "name": "Claude 3 Sonnet",
            "provider": "anthropic",
            "description": "Balanced Claude 3 model"
        },
        {
            "id": "claude-3-haiku-20240307",
            "name": "Claude 3 Haiku",
            "provider": "anthropic",
            "description": "Fastest Claude 3 model"
        }
    ]
    
    # Try to verify API key by making a test request
    try:
        test_url = f"{base_url or 'https://api.anthropic.com/v1'}/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        # Just verify the key is valid, don't actually send a message
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try a simple HEAD request or minimal POST to verify auth
            response = await client.post(
                test_url,
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "test"}]
                }
            )
            # If auth fails, raise error
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Anthropic API key")
            
            return common_models
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid Anthropic API key")
        # If other error, still return common models (user can try them)
        return common_models
    except Exception as e:
        logger.warning(f"Could not verify Anthropic API key: {e}")
        # Return common models anyway
        return common_models


class ModelDetectionRequest(BaseModel):
    """Request model for model detection"""
    provider: str = Field(..., description="Provider type (openai, anthropic, etc.)")
    api_key: str = Field(..., min_length=1, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom base URL")


@router.post("/detect-models")
async def detect_available_models(
    request: ModelDetectionRequest
):
    """
    Detect available models from an LLM provider using API key
    
    This endpoint queries the provider's API to fetch available models
    without storing the provider configuration.
    """
    logger.info(f"Model detection request: provider={request.provider}, base_url={request.base_url or 'default'}")
    
    try:
        if not request.api_key or not request.api_key.strip():
            raise HTTPException(
                status_code=400,
                detail="API key is required"
            )
        
        if request.provider == "openai":
            logger.debug("Fetching OpenAI models")
            models = await fetch_openai_models(request.api_key, request.base_url)
        elif request.provider == "anthropic":
            logger.debug("Fetching Anthropic models")
            models = await fetch_anthropic_models(request.api_key, request.base_url)
        elif request.provider == "azure":
            # Azure OpenAI uses same API structure as OpenAI
            if not request.base_url:
                raise HTTPException(
                    status_code=400,
                    detail="Base URL is required for Azure OpenAI"
                )
            logger.debug("Fetching Azure OpenAI models")
            models = await fetch_openai_models(request.api_key, request.base_url)
        else:
            logger.warning(f"Unsupported provider: {request.provider}")
            raise HTTPException(
                status_code=400,
                detail=f"Model detection not supported for provider: {request.provider}"
            )
        
        logger.info(f"Model detection successful: found {len(models)} models for {request.provider}")
        return {
            "provider": request.provider,
            "models": models,
            "count": len(models)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect models: {str(e)}"
        )


@router.get("/", response_model=LLMProviderListResponse)
async def list_llm_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all LLM providers with optional filtering
    """
    try:
        query = db.query(LLMProvider)
        
        # Apply filters
        if status:
            query = query.filter(LLMProvider.status == status)
        
        if provider:
            query = query.filter(LLMProvider.provider == provider)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get results
        providers = query.order_by(LLMProvider.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to response format
        provider_items = [
            LLMProviderListItem(
                id=provider.id,
                name=provider.name,
                provider=provider.provider,
                model=provider.model,
                status=provider.status,
                priority=provider.priority,
                is_default=provider.is_default,
                usage_count=provider.usage_count or "0",
                created_at=provider.created_at,
                api_key_masked=mask_api_key(provider.api_key) if provider.api_key else "***"  # Include masked API key
            )
            for provider in providers
        ]
        
        return LLMProviderListResponse(
            items=provider_items,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing LLM providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.get("/{provider_id}", response_model=LLMProviderResponse)
async def get_llm_provider(
    provider_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get specific LLM provider by ID
    """
    provider = db.query(LLMProvider).filter(LLMProvider.id == str(provider_id)).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    
    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider=provider.provider,
        model=provider.model,
        api_key=provider.api_key,  # Will be masked in response
        base_url=provider.base_url,
        status=provider.status,
        priority=provider.priority,
        config=provider.config or {},
        max_tokens=provider.max_tokens,
        temperature=provider.temperature,
        timeout=provider.timeout,
        description=provider.description,
        is_default=provider.is_default,
        usage_count=provider.usage_count or "0",
        cost_per_token=provider.cost_per_token,
        avg_response_time=provider.avg_response_time,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
        api_key_masked=mask_api_key(provider.api_key) if provider.api_key else "***"
    )


@router.post("/", response_model=LLMProviderResponse)
async def create_llm_provider(
    provider: LLMProviderCreate,
    db: Session = Depends(get_db)
):
    """
    Create new LLM provider
    """
    # If this is set as default, unset other defaults
    if provider.is_default:
        db.query(LLMProvider).filter(LLMProvider.is_default == True).update({"is_default": False})
    
    # Create provider
    db_provider = LLMProvider(
        name=provider.name,
        provider=provider.provider,
        model=provider.model,
        api_key=provider.api_key,  # TODO: Encrypt this
        base_url=provider.base_url,
        status=provider.status,
        priority=provider.priority,
        config=provider.config or {},
        max_tokens=provider.max_tokens,
        temperature=provider.temperature,
        timeout=provider.timeout,
        description=provider.description,
        is_default=provider.is_default
    )
    
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    
    return LLMProviderResponse(
        id=db_provider.id,
        name=db_provider.name,
        provider=db_provider.provider,
        model=db_provider.model,
        api_key=db_provider.api_key,
        base_url=db_provider.base_url,
        status=db_provider.status,
        priority=db_provider.priority,
        config=db_provider.config or {},
        max_tokens=db_provider.max_tokens,
        temperature=db_provider.temperature,
        timeout=db_provider.timeout,
        description=db_provider.description,
        is_default=db_provider.is_default,
        usage_count=db_provider.usage_count or "0",
        cost_per_token=db_provider.cost_per_token,
        avg_response_time=db_provider.avg_response_time,
        created_at=db_provider.created_at,
        updated_at=db_provider.updated_at,
        api_key_masked=mask_api_key(db_provider.api_key) if db_provider.api_key else "***"
    )


@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_llm_provider(
    provider_id: uuid.UUID,
    provider_update: LLMProviderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update existing LLM provider
    """
    db_provider = db.query(LLMProvider).filter(LLMProvider.id == str(provider_id)).first()
    
    if not db_provider:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    
    # If setting as default, unset other defaults
    if provider_update.is_default is True:
        db.query(LLMProvider).filter(LLMProvider.is_default == True).update({"is_default": False})
    
    # Update fields
    update_data = provider_update.dict(exclude_unset=True)
    
    # Handle API key separately (should be encrypted)
    # Only update API key if a new one is provided (not empty)
    if "api_key" in update_data and update_data["api_key"]:
        db_provider.api_key = update_data.pop("api_key")  # TODO: Encrypt this
    elif "api_key" in update_data:
        # Remove empty API key from update_data so it doesn't clear the existing key
        update_data.pop("api_key")
    
    for field, value in update_data.items():
        setattr(db_provider, field, value)
    
    db.commit()
    db.refresh(db_provider)
    
    return LLMProviderResponse(
        id=db_provider.id,
        name=db_provider.name,
        provider=db_provider.provider,
        model=db_provider.model,
        api_key=db_provider.api_key,
        base_url=db_provider.base_url,
        status=db_provider.status,
        priority=db_provider.priority,
        config=db_provider.config or {},
        max_tokens=db_provider.max_tokens,
        temperature=db_provider.temperature,
        timeout=db_provider.timeout,
        description=db_provider.description,
        is_default=db_provider.is_default,
        usage_count=db_provider.usage_count or "0",
        cost_per_token=db_provider.cost_per_token,
        avg_response_time=db_provider.avg_response_time,
        created_at=db_provider.created_at,
        updated_at=db_provider.updated_at,
        api_key_masked=mask_api_key(db_provider.api_key) if db_provider.api_key else "***"
    )


@router.delete("/{provider_id}")
async def delete_llm_provider(
    provider_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Delete LLM provider
    """
    provider = db.query(LLMProvider).filter(LLMProvider.id == str(provider_id)).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    
    db.delete(provider)
    db.commit()
    
    return {"message": "LLM provider deleted successfully"}


@router.post("/{provider_id}/test")
async def test_llm_provider(
    provider_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Test/sanity check an LLM provider by sending a simple test message
    
    Verifies that the API key, base URL, and model configuration work correctly.
    """
    provider = db.query(LLMProvider).filter(LLMProvider.id == str(provider_id)).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="LLM provider not found")
    
    if not provider.api_key:
        raise HTTPException(status_code=400, detail="API key not configured for this provider")
    
    test_message = "Hello! This is a test message from LoreGuard. Please respond with 'OK' if you can read this."
    
    try:
        start_time = time.time()
        
        if provider.provider == "openai" or (provider.provider == "azure" and provider.base_url):
            # OpenAI or Azure OpenAI
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
            
            payload = {
                "model": provider.model,
                "messages": [
                    {"role": "user", "content": test_message}
                ],
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                response_time = time.time() - start_time
                
                # Extract response text
                response_text = ""
                if "choices" in result and len(result["choices"]) > 0:
                    response_text = result["choices"][0].get("message", {}).get("content", "")
                
                return {
                    "success": True,
                    "provider_id": str(provider_id),
                    "provider_name": provider.name,
                    "test_message": test_message,
                    "response": response_text,
                    "response_time_seconds": round(response_time, 2),
                    "model_used": result.get("model", provider.model),
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
        
        elif provider.provider == "anthropic":
            # Anthropic Claude
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
                "model": provider.model,
                "max_tokens": 50,
                "messages": [
                    {"role": "user", "content": test_message}
                ]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                response_time = time.time() - start_time
                
                # Extract response text
                response_text = ""
                if "content" in result and len(result["content"]) > 0:
                    response_text = result["content"][0].get("text", "")
                
                return {
                    "success": True,
                    "provider_id": str(provider_id),
                    "provider_name": provider.name,
                    "test_message": test_message,
                    "response": response_text,
                    "response_time_seconds": round(response_time, 2),
                    "model_used": result.get("model", provider.model),
                    "tokens_used": result.get("usage", {}).get("input_tokens", 0) + result.get("usage", {}).get("output_tokens", 0)
                }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Test/sanity check not yet supported for provider type: {provider.provider}"
            )
    
    except httpx.HTTPStatusError as e:
        error_text = e.response.text[:500] if e.response.text else "No error details"
        logger.error(f"Provider test failed: {e.response.status_code} - {error_text}")
        
        if e.response.status_code == 401:
            return {
                "success": False,
                "provider_id": str(provider_id),
                "provider_name": provider.name,
                "error": "Invalid API key. Please check your API key.",
                "error_code": 401
            }
        elif e.response.status_code == 404:
            return {
                "success": False,
                "provider_id": str(provider_id),
                "provider_name": provider.name,
                "error": f"Endpoint not found. Check your base URL: {provider.base_url or 'default'}",
                "error_code": 404
            }
        else:
            return {
                "success": False,
                "provider_id": str(provider_id),
                "provider_name": provider.name,
                "error": f"API request failed: {e.response.status_code} - {error_text[:200]}",
                "error_code": e.response.status_code
            }
    
    except httpx.TimeoutException:
        return {
            "success": False,
            "provider_id": str(provider_id),
            "provider_name": provider.name,
            "error": "Request timed out. Check your network connection and API endpoint.",
            "error_code": 504
        }
    
    except Exception as e:
        logger.error(f"Provider test error: {e}", exc_info=True)
        return {
            "success": False,
            "provider_id": str(provider_id),
            "provider_name": provider.name,
            "error": f"Test failed: {str(e)}",
            "error_code": 500
        }


@router.get("/default/active", response_model=LLMProviderResponse)
async def get_active_provider(
    db: Session = Depends(get_db)
):
    """
    Get the currently active/default LLM provider
    """
    # Try to get default provider first
    provider = db.query(LLMProvider).filter(LLMProvider.is_default == True).first()
    
    # If no default, get first active provider
    if not provider:
        provider = db.query(LLMProvider).filter(LLMProvider.status == "active").first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="No active LLM provider found")
    
    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider=provider.provider,
        model=provider.model,
        api_key=provider.api_key,
        base_url=provider.base_url,
        status=provider.status,
        priority=provider.priority,
        config=provider.config or {},
        max_tokens=provider.max_tokens,
        temperature=provider.temperature,
        timeout=provider.timeout,
        description=provider.description,
        is_default=provider.is_default,
        usage_count=provider.usage_count or "0",
        cost_per_token=provider.cost_per_token,
        avg_response_time=provider.avg_response_time,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
        api_key_masked=mask_api_key(provider.api_key) if provider.api_key else "***"
    )
