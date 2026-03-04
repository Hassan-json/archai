"""
API Gateway Service - Request Routing and Load Balancing
Routes requests to appropriate microservices
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Calculator API Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
CALCULATOR_SERVICE_URL = os.getenv("CALCULATOR_SERVICE_URL", "http://calculator-service:8001")
HISTORY_SERVICE_URL = os.getenv("HISTORY_SERVICE_URL", "http://history-service:8002")

class ServiceRegistry:
    """Service registry for managing service endpoints"""
    
    def __init__(self):
        self.services = {
            'calculator': CALCULATOR_SERVICE_URL,
            'history': HISTORY_SERVICE_URL
        }
    
    def get_service_url(self, service: str) -> str:
        """Get service URL"""
        return self.services.get(service)
    
    async def health_check_service(self, service: str) -> bool:
        """Check if service is healthy"""
        try:
            url = self.get_service_url(service)
            if not url:
                return False
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed for {service}: {str(e)}")
            return False

# Initialize service registry
registry = ServiceRegistry()

@app.post("/api/calculate")
async def calculate(request: Dict[str, Any]):
    """Route calculation requests to calculator service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{CALCULATOR_SERVICE_URL}/calculate",
                json=request
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
    except httpx.RequestError as e:
        logger.error(f"Request to calculator service failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Calculator service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/history")
async def get_history():
    """Route history requests to history service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{HISTORY_SERVICE_URL}/history")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
    except httpx.RequestError as e:
        logger.error(f"Request to history service failed: {str(e)}")
        raise HTTPException(status_code=503, detail="History service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/history")
async def clear_history():
    """Route history clear requests to history service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{HISTORY_SERVICE_URL}/history")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
    except httpx.RequestError as e:
        logger.error(f"Request to history service failed: {str(e)}")
        raise HTTPException(status_code=503, detail="History service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Gateway health check"""
    calculator_healthy = await registry.health_check_service('calculator')
    history_healthy = await registry.health_check_service('history')
    
    return {
        "status": "healthy" if calculator_healthy and history_healthy else "degraded",
        "services": {
            "calculator": "healthy" if calculator_healthy else "unhealthy",
            "history": "healthy" if history_healthy else "unhealthy"
        }
    }

@app.get("/api/health")
async def api_health():
    """API health endpoint for clients"""
    return await health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)