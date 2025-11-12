"""
Tool Executor Service

Executes tools/functions called by the LLM assistant.
Makes API calls to other LoreGuard services to perform actions.
"""

import logging
import httpx
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.context_service import ContextRetrievalService

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools/functions for the AI assistant"""
    
    def __init__(self, db: Session):
        self.db = db
        self.context_service = ContextRetrievalService(db)
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool/function
        
        Args:
            function_name: Name of the function to execute
            arguments: Function arguments
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing tool: {function_name} with args: {arguments}")
        
        try:
            # Route to appropriate handler
            if function_name == "get_rubric_details":
                return await self._get_rubric_details(arguments)
            elif function_name == "search_artifacts":
                return await self._search_artifacts(arguments)
            elif function_name == "get_artifact_details":
                return await self._get_artifact_details(arguments)
            elif function_name == "list_sources":
                return await self._list_sources(arguments)
            elif function_name == "trigger_source_crawl":
                return await self._trigger_source_crawl(arguments)
            elif function_name == "get_job_status":
                return await self._get_job_status(arguments)
            elif function_name == "list_active_jobs":
                return await self._list_active_jobs(arguments)
            elif function_name == "evaluate_artifact":
                return await self._evaluate_artifact(arguments)
            elif function_name == "get_system_health":
                return await self._get_system_health(arguments)
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
                
        except Exception as e:
            logger.error(f"Error executing tool {function_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_rubric_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get rubric details"""
        version = args.get("version", "active")
        
        try:
            if version == "active":
                url = f"{settings.API_SERVICE_URL}/api/v1/rubrics/active"
            else:
                # Find rubric by version
                from models.rubric import Rubric
                rubric = self.db.query(Rubric).filter(Rubric.version == version).first()
                if not rubric:
                    return {"success": False, "error": f"Rubric {version} not found"}
                url = f"{settings.API_SERVICE_URL}/api/v1/rubrics/{rubric.id}"
            
            logger.info(f"Calling API endpoint: {url}")
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {settings.API_SERVICE_URL}. Check if API service is running."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout to {settings.API_SERVICE_URL}."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def _search_artifacts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search artifacts"""
        query = args.get("query", "")
        limit = args.get("limit", 5)
        
        try:
            results = self.context_service.search_artifacts(query, limit)
            return {
                "success": True,
                "data": {
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_artifact_details(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get artifact details"""
        artifact_id = args.get("artifact_id")
        
        try:
            details = self.context_service.get_artifact_details(artifact_id)
            
            if not details:
                return {"success": False, "error": f"Artifact {artifact_id} not found"}
            
            return {
                "success": True,
                "data": details
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_sources(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List sources"""
        status_filter = args.get("status_filter", "all")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/sources/"
            if status_filter and status_filter != "all":
                url += f"?status={status_filter}"
            
            logger.info(f"Calling API endpoint: {url}")
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            return {
                "success": True,
                "data": {
                    "sources": data.get("items", []),
                    "count": data.get("total", 0)
                }
            }
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {settings.API_SERVICE_URL}. Check if API service is running and accessible."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout to {settings.API_SERVICE_URL}. Service may be slow or unresponsive."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error calling {url}: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def _trigger_source_crawl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger source crawl"""
        source_id = args.get("source_id")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/sources/{source_id}/trigger"
            logger.info(f"Calling API endpoint: {url}")
            response = await self.http_client.post(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {settings.API_SERVICE_URL}. Check if API service is running."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout to {settings.API_SERVICE_URL}."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def _get_job_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get job status"""
        job_id = args.get("job_id")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/jobs/{job_id}"
            logger.info(f"Calling API endpoint: {url}")
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {settings.API_SERVICE_URL}. Check if API service is running."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout to {settings.API_SERVICE_URL}."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def _list_active_jobs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List active jobs"""
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/jobs/active/list"
            logger.info(f"Calling API endpoint: {url}")
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {settings.API_SERVICE_URL}. Check if API service is running."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout to {settings.API_SERVICE_URL}."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def _evaluate_artifact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger artifact evaluation"""
        artifact_id = args.get("artifact_id")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/artifacts/{artifact_id}/evaluate"
            logger.info(f"Calling API endpoint: {url}")
            response = await self.http_client.post(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {settings.API_SERVICE_URL}. Check if API service is running."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout to {settings.API_SERVICE_URL}."
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} from {url}: {e.response.text}"
            logger.error(f"{error_msg} Error: {e}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"{error_msg}", exc_info=True)
            return {"success": False, "error": error_msg}
    
    async def _get_system_health(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system health"""
        health_data = {
            "api_service": {"status": "unknown"},
            "normalize_service": {"status": "unknown"},
            "jobs": {}
        }
        
        errors = []
        
        # Check API service
        try:
            logger.info(f"Checking API service health: {settings.API_SERVICE_URL}/health")
            api_health = await self.http_client.get(f"{settings.API_SERVICE_URL}/health", timeout=5.0)
            if api_health.status_code == 200:
                health_data["api_service"] = api_health.json()
            else:
                health_data["api_service"] = {"status": "unhealthy", "status_code": api_health.status_code}
        except httpx.ConnectError as e:
            health_data["api_service"] = {"status": "unreachable", "error": "Connection failed"}
            errors.append(f"API service connection failed: {e}")
        except httpx.TimeoutException as e:
            health_data["api_service"] = {"status": "timeout", "error": "Request timeout"}
            errors.append(f"API service timeout: {e}")
        except Exception as e:
            health_data["api_service"] = {"status": "error", "error": str(e)}
            errors.append(f"API service error: {e}")
        
        # Check normalize service
        try:
            logger.info(f"Checking Normalize service health: {settings.NORMALIZE_SERVICE_URL}/health")
            normalize_health = await self.http_client.get(f"{settings.NORMALIZE_SERVICE_URL}/health", timeout=5.0)
            if normalize_health.status_code == 200:
                health_data["normalize_service"] = normalize_health.json()
            else:
                health_data["normalize_service"] = {"status": "unhealthy", "status_code": normalize_health.status_code}
        except httpx.ConnectError as e:
            health_data["normalize_service"] = {"status": "unreachable", "error": "Connection failed"}
            errors.append(f"Normalize service connection failed: {e}")
        except httpx.TimeoutException as e:
            health_data["normalize_service"] = {"status": "timeout", "error": "Request timeout"}
            errors.append(f"Normalize service timeout: {e}")
        except Exception as e:
            health_data["normalize_service"] = {"status": "error", "error": str(e)}
            errors.append(f"Normalize service error: {e}")
        
        # Get job health summary
        try:
            logger.info(f"Getting jobs health summary: {settings.API_SERVICE_URL}/api/v1/jobs/health/summary")
            jobs_health = await self.http_client.get(f"{settings.API_SERVICE_URL}/api/v1/jobs/health/summary", timeout=5.0)
            if jobs_health.status_code == 200:
                health_data["jobs"] = jobs_health.json()
            else:
                health_data["jobs"] = {"error": f"HTTP {jobs_health.status_code}"}
        except httpx.ConnectError as e:
            health_data["jobs"] = {"error": "Connection failed"}
            errors.append(f"Jobs health check connection failed: {e}")
        except httpx.TimeoutException as e:
            health_data["jobs"] = {"error": "Request timeout"}
            errors.append(f"Jobs health check timeout: {e}")
        except Exception as e:
            health_data["jobs"] = {"error": str(e)}
            errors.append(f"Jobs health check error: {e}")
        
        # Return success if at least one service responded, but include errors
        if errors:
            logger.warning(f"System health check completed with errors: {errors}")
        
        return {
            "success": True,
            "data": health_data,
            "warnings": errors if errors else None
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()

