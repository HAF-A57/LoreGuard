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
            
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _trigger_source_crawl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger source crawl"""
        source_id = args.get("source_id")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/sources/{source_id}/trigger"
            response = await self.http_client.post(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_job_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get job status"""
        job_id = args.get("job_id")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/jobs/{job_id}"
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_active_jobs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List active jobs"""
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/jobs/active/list"
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _evaluate_artifact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger artifact evaluation"""
        artifact_id = args.get("artifact_id")
        
        try:
            url = f"{settings.API_SERVICE_URL}/api/v1/artifacts/{artifact_id}/evaluate"
            response = await self.http_client.post(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_system_health(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system health"""
        try:
            # Check API service
            api_health = await self.http_client.get(f"{settings.API_SERVICE_URL}/health")
            
            # Check normalize service
            normalize_health = await self.http_client.get(f"{settings.NORMALIZE_SERVICE_URL}/health")
            
            # Get job health summary
            jobs_health = await self.http_client.get(f"{settings.API_SERVICE_URL}/api/v1/jobs/health/summary")
            
            return {
                "success": True,
                "data": {
                    "api_service": api_health.json() if api_health.status_code == 200 else {"status": "unhealthy"},
                    "normalize_service": normalize_health.json() if normalize_health.status_code == 200 else {"status": "unhealthy"},
                    "jobs": jobs_health.json() if jobs_health.status_code == 200 else {}
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()

