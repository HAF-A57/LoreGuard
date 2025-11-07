"""
LLM Evaluation Service for Artifact Evaluation

Evaluates artifacts using configured LLM providers against rubrics.
Supports OpenAI, Anthropic, Azure OpenAI, and custom providers.
Integrates with prompt templates for flexible prompt management.
"""

import json
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
import httpx
import boto3
from botocore.exceptions import ClientError

from models.artifact import Artifact
from models.evaluation import Evaluation
from models.rubric import Rubric
from models.llm_provider import LLMProvider
from models.prompt_template import PromptTemplate
from core.config import settings

logger = logging.getLogger(__name__)


class LLMEvaluationService:
    """Service for evaluating artifacts using configured LLM providers"""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize LLM evaluation service
        
        Args:
            db: Optional database session (will create if not provided)
        """
        self.db = db
        
        # Initialize MinIO/S3 client for fetching normalized content
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            use_ssl=False
        )
    
    async def evaluate_artifact(
        self,
        artifact_id: str,
        rubric_version: str = "latest",
        provider_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Evaluation:
        """
        Evaluate an artifact using configured LLM provider against a rubric
        
        Args:
            artifact_id: ID of artifact to evaluate
            rubric_version: Rubric version to use (default: "latest" for active)
            provider_id: Optional specific provider ID (default: uses default/active provider)
            db: Database session (uses self.db if not provided)
            
        Returns:
            Evaluation object with scores and label
            
        Raises:
            ValueError: If artifact, rubric, or provider not found
            RuntimeError: If LLM evaluation fails
        """
        session = db or self.db
        if not session:
            raise ValueError("Database session required")
        
        # Load artifact
        artifact = session.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")
        
        # Load rubric
        if rubric_version == "latest":
            rubric = session.query(Rubric).filter(Rubric.is_active == True).first()
        else:
            rubric = session.query(Rubric).filter(Rubric.version == rubric_version).first()
        
        if not rubric:
            raise ValueError(f"Rubric {rubric_version} not found")
        
        # Load LLM provider
        provider = self._get_provider(session, provider_id)
        if not provider:
            raise ValueError("No active LLM provider found. Configure a provider in Settings.")
        
        # Verify provider is active
        if provider.status != "active":
            raise ValueError(f"LLM provider {provider.name} is not active (status: {provider.status})")
        
        # Check if artifact is normalized
        if not artifact.normalized_ref:
            raise ValueError(f"Artifact {artifact_id} must be normalized before evaluation")
        
        # Fetch normalized content from MinIO
        normalized_content = self._fetch_normalized_content(artifact.normalized_ref)
        if not normalized_content:
            raise ValueError(f"Could not fetch normalized content for artifact {artifact_id}")
        
        # Get metadata
        metadata = artifact.document_metadata
        metadata_dict = {
            "title": metadata.title if metadata else None,
            "authors": json.loads(metadata.authors) if metadata and metadata.authors else [],
            "organization": metadata.organization if metadata else None,
            "publication_date": str(metadata.pub_date) if metadata and metadata.pub_date else None,
            "topics": json.loads(metadata.topics) if metadata and metadata.topics else [],
            "language": metadata.language if metadata else "en",
            "geo_location": metadata.geo_location if metadata else None,
        }
        
        # Load prompt templates from rubric references
        system_prompt, user_prompt, prompt_ref = self._build_prompts_from_templates(
            rubric=rubric,
            artifact=artifact,
            content=normalized_content,
            metadata=metadata_dict,
            db=session
        )
        
        # Perform LLM evaluation based on provider type
        try:
            if provider.provider in ["openai", "azure"]:
                result_data = await self._evaluate_openai(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=provider.model,
                    rubric=rubric
                )
            elif provider.provider == "anthropic":
                result_data = await self._evaluate_anthropic(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=provider.model
                )
            else:
                raise ValueError(f"Unsupported provider type: {provider.provider}")
            
            # Calculate total weighted score
            total_score = self._calculate_total_score(result_data.get("scores", {}), rubric)
            
            # Determine label based on thresholds
            label = rubric.get_label_for_score(total_score)
            
            # Create evaluation record
            evaluation = Evaluation(
                artifact_id=str(artifact_id),
                rubric_version=rubric.version,
                model_id=result_data.get("model_id", provider.model),
                scores=result_data.get("scores", {}),
                label=label,
                confidence=Decimal(str(result_data.get("confidence", 0.0))),
                prompt_ref=prompt_ref
            )
            
            session.add(evaluation)
            session.commit()
            session.refresh(evaluation)
            
            # Increment template usage count
            if prompt_ref:
                self._increment_template_usage(session, prompt_ref)
            
            logger.info(f"Evaluation completed for artifact {artifact_id}: {label} (score: {total_score:.2f})")
            return evaluation
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:500] if e.response.text else "No error details"
            logger.error(f"LLM API error: {e.response.status_code} - {error_text}")
            raise RuntimeError(f"LLM evaluation failed: {e.response.status_code} - {error_text}")
        except Exception as e:
            logger.error(f"LLM evaluation error: {e}", exc_info=True)
            raise RuntimeError(f"Evaluation failed: {str(e)}")
    
    def _build_prompts_from_templates(
        self,
        rubric: Rubric,
        artifact: Artifact,
        content: str,
        metadata: Dict[str, Any],
        db: Session
    ) -> tuple[str, str, Optional[str]]:
        """
        Build prompts using prompt templates referenced in rubric
        
        Args:
            rubric: Rubric with prompt references
            artifact: Artifact being evaluated
            content: Normalized document content
            metadata: Document metadata dictionary
            db: Database session
            
        Returns:
            Tuple of (system_prompt, user_prompt, prompt_reference_id)
        """
        # Get prompt reference from rubric (default to evaluation prompt)
        prompt_ref_id = None
        if rubric.prompts and isinstance(rubric.prompts, dict):
            prompt_ref_id = rubric.prompts.get("evaluation")
        
        # If no reference in rubric, try to get default evaluation template
        if not prompt_ref_id:
            default_template = db.query(PromptTemplate).filter(
                PromptTemplate.type == "evaluation",
                PromptTemplate.is_default == True,
                PromptTemplate.is_active == True
            ).first()
            if default_template:
                prompt_ref_id = default_template.reference_id
        
        # Load template if reference exists
        template = None
        if prompt_ref_id:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.reference_id == prompt_ref_id,
                PromptTemplate.is_active == True
            ).first()
        
        if template:
            # Use template to build prompts
            system_prompt = template.system_prompt or ""
            
            # Prepare variables for template substitution
            content_preview = content[:8000] + ("..." if len(content) > 8000 else "")
            
            # Format rubric categories as JSON
            categories_dict = rubric.categories if isinstance(rubric.categories, dict) else {}
            rubric_categories_json = json.dumps(categories_dict, indent=2)
            
            # Prepare clarification signals (if available)
            clarification_signals = "None available"
            if artifact.clarification and artifact.clarification.signals:
                clarification_signals = json.dumps(artifact.clarification.signals, indent=2)
            
            # Substitute variables in user prompt template
            try:
                user_prompt = template.user_prompt_template.format(
                    artifact_uri=artifact.uri,
                    title=metadata.get("title", "Unknown"),
                    authors=", ".join(metadata.get("authors", [])) if metadata.get("authors") else "Unknown",
                    organization=metadata.get("organization", "Unknown"),
                    publication_date=metadata.get("publication_date", "Unknown"),
                    topics=", ".join(metadata.get("topics", [])) if metadata.get("topics") else "Unknown",
                    language=metadata.get("language", "en"),
                    clarification_signals=clarification_signals,
                    document_content_preview=content_preview,
                    rubric_categories_json=rubric_categories_json,
                    signal_min=str(rubric.thresholds.get("signal_min", 3.8)),
                    review_min=str(rubric.thresholds.get("review_min", 2.8))
                )
            except KeyError as e:
                logger.warning(f"Missing variable in prompt template: {e}. Using fallback prompt.")
                # Fallback to basic prompt construction
                system_prompt, user_prompt = self._build_fallback_prompts(rubric, artifact, content, metadata)
                prompt_ref_id = None
        else:
            # Fallback to built-in prompt construction if no template found
            logger.info("No prompt template found, using built-in prompt construction")
            system_prompt, user_prompt = self._build_fallback_prompts(rubric, artifact, content, metadata)
            prompt_ref_id = None
        
        return system_prompt, user_prompt, prompt_ref_id
    
    def _build_fallback_prompts(
        self,
        rubric: Rubric,
        artifact: Artifact,
        content: str,
        metadata: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Build prompts using built-in logic (fallback when templates not available)
        
        Args:
            rubric: Rubric with evaluation criteria
            artifact: Artifact being evaluated
            content: Normalized document content
            metadata: Document metadata dictionary
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Build system prompt from rubric
        system_prompt = f"""You are an expert evaluator for military wargaming research documents.
Your task is to evaluate documents against specific criteria and provide structured scores.

Rubric Version: {rubric.version}

Categories and Weights:
{json.dumps(rubric.categories, indent=2)}

Thresholds:
- Signal: >= {rubric.thresholds.get('signal_min', 3.8)}
- Review: >= {rubric.thresholds.get('review_min', 2.8)}
- Noise: < {rubric.thresholds.get('review_min', 2.8)}

Score each category from 0-5 based on the guidance provided.
Provide an overall label (Signal/Review/Noise) and confidence score (0.0-1.0).
"""
        
        # Build user prompt with artifact context
        content_preview = content[:5000] + ("..." if len(content) > 5000 else "")
        
        user_prompt = f"""Evaluate the following document:

URI: {artifact.uri}
Title: {metadata.get('title', 'Unknown')}
Authors: {', '.join(metadata.get('authors', [])) if metadata.get('authors') else 'Unknown'}
Organization: {metadata.get('organization', 'Unknown')}
Publication Date: {metadata.get('publication_date', 'Unknown')}

Content:
{content_preview}

Evaluate against the rubric categories and provide structured scores."""
        
        return system_prompt, user_prompt
    
    async def _evaluate_openai(
        self,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str,
        model: str,
        rubric: 'Rubric' = None
    ) -> Dict[str, Any]:
        """Evaluate using OpenAI/Azure OpenAI API"""
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
        
        # Use function calling for structured output
        function_schema = {
            "name": "evaluate_document",
            "description": "Evaluate a document and provide structured scores",
            "parameters": {
                "type": "object",
                "properties": {
                    "scores": {
                        "type": "object",
                        "description": "Scores for each category",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number", "minimum": 0, "maximum": 5},
                                "reasoning": {"type": "string"}
                            },
                            "required": ["score", "reasoning"]
                        }
                    },
                    "label": {
                        "type": "string",
                        "enum": ["Signal", "Review", "Noise"],
                        "description": "Overall classification"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence in evaluation"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of evaluation"
                    }
                },
                "required": ["scores", "label", "confidence", "summary"]  # scores is REQUIRED
            }
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "functions": [function_schema],
            "function_call": {"name": "evaluate_document"},
            "temperature": float(provider.temperature) if provider.temperature else 0.2
        }
        
        async with httpx.AsyncClient(timeout=float(provider.timeout) if provider.timeout else 30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Log the raw response for debugging
            logger.info(f"[LLM DEBUG] OpenAI response received")
            logger.info(f"[LLM DEBUG] Model: {result.get('model', 'unknown')}")
            
            # Extract function call arguments
            message = result["choices"][0]["message"]
            logger.info(f"[LLM DEBUG] Message keys: {list(message.keys())}")
            
            if "function_call" in message:
                function_call = message["function_call"]
                logger.info(f"[LLM DEBUG] Function called: {function_call.get('name')}")
                logger.info(f"[LLM DEBUG] Arguments (first 500 chars): {function_call.get('arguments', '')[:500]}")
                
                function_args = json.loads(message["function_call"]["arguments"])
                scores = function_args.get("scores", {})
                
                logger.info(f"[LLM DEBUG] Parsed scores keys: {list(scores.keys()) if scores else 'EMPTY'}")
                logger.info(f"[LLM DEBUG] Label: {function_args.get('label')}, Confidence: {function_args.get('confidence')}")
                
                # If scores is empty (GPT-4 sometimes ignores requirement for Noise), generate default zeros
                if not scores:
                    logger.warning("[LLM] Scores missing from response, generating default zeros for all categories")
                    # Get rubric categories and generate 0 scores
                    scores = {cat: {"score": 0, "reasoning": "No detailed scoring provided by LLM for low-quality content"} 
                             for cat in rubric.categories.keys()}
                
                return {
                    "scores": scores,
                    "label": function_args.get("label", "Review"),
                    "confidence": function_args.get("confidence", 0.5),
                    "summary": function_args.get("summary", ""),
                    "model_id": result.get("model", model)
                }
            else:
                # Fallback: try to parse JSON from content
                content = message.get("content", "")
                try:
                    parsed = json.loads(content)
                    return {
                        "scores": parsed.get("scores", {}),
                        "label": parsed.get("label", "Review"),
                        "confidence": parsed.get("confidence", 0.5),
                        "summary": parsed.get("summary", ""),
                        "model_id": result.get("model", model)
                    }
                except json.JSONDecodeError:
                    raise RuntimeError(f"Could not parse LLM response as JSON: {content[:200]}")
    
    async def _evaluate_anthropic(
        self,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str,
        model: str
    ) -> Dict[str, Any]:
        """Evaluate using Anthropic Claude API"""
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
            "max_tokens": int(provider.max_tokens) if provider.max_tokens else 4000,
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
                parsed = json.loads(content)
                return {
                    "scores": parsed.get("scores", {}),
                    "label": parsed.get("label", "Review"),
                    "confidence": parsed.get("confidence", 0.5),
                    "summary": parsed.get("summary", ""),
                    "model_id": result.get("model", model)
                }
            except json.JSONDecodeError:
                # Try to extract JSON from text if it's embedded
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        return {
                            "scores": parsed.get("scores", {}),
                            "label": parsed.get("label", "Review"),
                            "confidence": parsed.get("confidence", 0.5),
                            "summary": parsed.get("summary", ""),
                            "model_id": result.get("model", model)
                        }
                    except json.JSONDecodeError:
                        pass
                
                raise RuntimeError(f"Could not parse Anthropic response as JSON: {content[:200]}")
    
    def _calculate_total_score(self, scores: Dict[str, Dict], rubric: Rubric) -> float:
        """Calculate weighted total score"""
        if not scores or not rubric.categories:
            return 0.0
        
        total = 0.0
        categories = rubric.categories if isinstance(rubric.categories, dict) else {}
        
        for category_name, score_data in scores.items():
            if category_name in categories:
                weight = categories[category_name].get('weight', 0)
                score = score_data.get('score', 0) if isinstance(score_data, dict) else score_data
                total += score * weight
        
        return total
    
    def _get_provider(self, db: Session, provider_id: Optional[str] = None) -> Optional[LLMProvider]:
        """Get LLM provider (default or specified)"""
        if provider_id:
            return db.query(LLMProvider).filter(LLMProvider.id == str(provider_id)).first()
        
        # Try default provider first
        provider = db.query(LLMProvider).filter(LLMProvider.is_default == True).first()
        if provider and provider.status == "active":
            return provider
        
        # Fallback to first active provider
        return db.query(LLMProvider).filter(LLMProvider.status == "active").first()
    
    def _fetch_normalized_content(self, normalized_ref: str) -> str:
        """Fetch normalized content from MinIO/S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=normalized_ref
            )
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            logger.error(f"Failed to fetch normalized content from MinIO: {e}")
            raise RuntimeError(f"Could not fetch normalized content: {str(e)}")
    
    def _increment_template_usage(self, db: Session, prompt_ref_id: str):
        """Increment usage count for a prompt template"""
        try:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.reference_id == prompt_ref_id
            ).first()
            
            if template:
                current_count = int(template.usage_count) if template.usage_count else 0
                template.usage_count = str(current_count + 1)
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to increment template usage count: {e}")
            # Don't fail evaluation if usage tracking fails
            db.rollback()

