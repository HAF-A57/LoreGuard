"""
LLM Client Service

Client for interacting with LLM providers with function/tool calling support.
Supports OpenAI and Anthropic models with dynamic provider selection.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from openai import OpenAI, AsyncOpenAI
from anthropic import Anthropic
import tiktoken

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM interactions with function calling"""
    
    def __init__(self, provider_config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM client
        
        Args:
            provider_config: Provider configuration (from database)
                - provider: 'openai' or 'anthropic'
                - api_key: API key
                - model: Model name
                - base_url: Optional base URL
                - temperature: Optional temperature
                - max_tokens: Optional max tokens
        """
        self.provider_config = provider_config or {}
        self.provider_type = self.provider_config.get('provider', 'openai')
        self.model = self.provider_config.get('model', settings.DEFAULT_LLM_MODEL)
        
        # Handle temperature (may be string or None)
        temp_val = self.provider_config.get('temperature')
        if temp_val is not None:
            try:
                self.temperature = float(temp_val)
            except (ValueError, TypeError):
                self.temperature = settings.DEFAULT_LLM_TEMPERATURE
        else:
            self.temperature = settings.DEFAULT_LLM_TEMPERATURE
        
        # Handle max_tokens (may be string or None)
        max_tok_val = self.provider_config.get('max_tokens')
        if max_tok_val is not None:
            try:
                self.max_tokens = int(max_tok_val)
            except (ValueError, TypeError):
                self.max_tokens = settings.MAX_COMPLETION_TOKENS
        else:
            self.max_tokens = settings.MAX_COMPLETION_TOKENS
        
        # Initialize clients based on provider
        self._initialize_clients()
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except:
            # Fallback to cl100k_base (GPT-4 encoding)
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _initialize_clients(self):
        """Initialize LLM provider clients"""
        if self.provider_type in ['openai', 'azure']:
            api_key = self.provider_config.get('api_key')
            base_url = self.provider_config.get('base_url')
            
            if api_key:
                self.openai_client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url if base_url else None
                )
            else:
                # Use environment variable or default
                self.openai_client = AsyncOpenAI()
        
        elif self.provider_type == 'anthropic':
            api_key = self.provider_config.get('api_key')
            if api_key:
                self.anthropic_client = Anthropic(api_key=api_key)
            else:
                self.anthropic_client = Anthropic()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Rough estimation: ~4 chars per token
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Count total tokens in messages list"""
        total = 0
        for message in messages:
            # Count role and content
            total += self.count_tokens(message.get('role', ''))
            total += self.count_tokens(message.get('content', ''))
            
            # Account for message formatting overhead
            total += 4  # Rough overhead per message
        
        return total
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate chat completion
        
        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tools/functions
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            Dictionary with response, usage, and tool calls
        """
        
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if self.provider_type in ['openai', 'azure']:
                return await self._openai_completion(messages, tools, temp, max_tok)
            elif self.provider_type == 'anthropic':
                return await self._anthropic_completion(messages, tools, temp, max_tok)
            else:
                raise ValueError(f"Unsupported provider type: {self.provider_type}")
                
        except Exception as e:
            logger.error(f"Error in chat completion: {e}", exc_info=True)
            raise
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """OpenAI-style completion"""
        
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"
        
        response = await self.openai_client.chat.completions.create(**request_params)
        
        # Extract response
        message = response.choices[0].message
        
        result = {
            "role": message.role,
            "content": message.content or "",
            "tool_calls": None,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason
        }
        
        # Extract tool calls if present
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        
        return result
    
    async def _anthropic_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Anthropic Claude completion"""
        
        # Convert OpenAI format to Anthropic format
        # Anthropic separates system messages
        system_message = None
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        request_params = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if system_message:
            request_params["system"] = system_message
        
        # Anthropic uses 'tools' parameter similar to OpenAI
        if tools:
            # Convert OpenAI tool format to Anthropic format
            anthropic_tools = []
            for tool in tools:
                if tool["type"] == "function":
                    anthropic_tools.append({
                        "name": tool["function"]["name"],
                        "description": tool["function"].get("description", ""),
                        "input_schema": tool["function"].get("parameters", {})
                    })
            request_params["tools"] = anthropic_tools
        
        response = self.anthropic_client.messages.create(**request_params)
        
        # Convert Anthropic response to OpenAI format for consistency
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input)
                    }
                })
        
        result = {
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls if tool_calls else None,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "model": response.model,
            "finish_reason": response.stop_reason
        }
        
        return result
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools/functions for the assistant
        
        Returns OpenAI function calling format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_rubric_details",
                    "description": "Get detailed information about a specific rubric version or the active rubric",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "version": {
                                "type": "string",
                                "description": "Rubric version (e.g., 'v0.1'). Use 'active' for the currently active rubric."
                            }
                        },
                        "required": ["version"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_artifacts",
                    "description": "Search for artifacts by title, organization, or topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (title, organization, or topic keywords)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_artifact_details",
                    "description": "Get detailed information about a specific artifact including metadata and evaluation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "artifact_id": {
                                "type": "string",
                                "description": "UUID of the artifact"
                            }
                        },
                        "required": ["artifact_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_sources",
                    "description": "List all configured data sources with their status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status_filter": {
                                "type": "string",
                                "description": "Filter by status (active, paused, error)",
                                "enum": ["active", "paused", "error", "all"]
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_source_crawl",
                    "description": "Trigger a manual crawl for a specific source",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "string",
                                "description": "UUID of the source to crawl"
                            }
                        },
                        "required": ["source_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_job_status",
                    "description": "Get status and details of a specific job",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "job_id": {
                                "type": "string",
                                "description": "UUID of the job"
                            }
                        },
                        "required": ["job_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_active_jobs",
                    "description": "List all currently active (running or pending) jobs",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_artifact",
                    "description": "Trigger evaluation for a specific artifact using the active rubric",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "artifact_id": {
                                "type": "string",
                                "description": "UUID of the artifact to evaluate"
                            }
                        },
                        "required": ["artifact_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_health",
                    "description": "Get overall system health status including all services",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

