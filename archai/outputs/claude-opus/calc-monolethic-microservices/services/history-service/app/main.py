"""
History Service - Data Persistence Microservice
Manages calculation history storage and retrieval
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="History Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryRepository:
    """Repository for managing calculation history"""
    
    def __init__(self, storage_file: str = "history.json"):
        self.storage_file = storage_file
        self._history = self._load_history()
    
    def _load_history(self) -> List[dict]:
        """Load history from file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load history: {str(e)}")
        return []
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self._history, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save history: {str(e)}")
    
    def add_calculation(self, expression: str, result: float, timestamp: str) -> dict:
        """Add a calculation to history"""
        calculation = {
            'expression': expression,
            'result': result,
            'timestamp': timestamp
        }
        self._history.append(calculation)
        self._save_history()
        logger.info(f"Added calculation: {expression} = {result}")
        return calculation
    
    def get_history(self) -> List[dict]:
        """Get all calculation history"""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear all calculation history"""
        self._history.clear()
        self._save_history()
        logger.info("Cleared calculation history")
    
    def get_last_result(self) -> Optional[dict]:
        """Get the last calculation result"""
        return self._history[-1] if self._history else None

# Initialize repository
history_repo = HistoryRepository()

@app.post("/history")
async def add_calculation(request: dict):
    """Add calculation to history"""
    try:
        expression = request.get('expression')
        result = request.get('result')
        timestamp = request.get('timestamp', datetime.now().isoformat())
        
        if not expression or result is None:
            raise HTTPException(status_code=400, detail="Expression and result are required")
        
        calculation = history_repo.add_calculation(expression, result, timestamp)
        
        return {
            'success': True,
            'data': calculation
        }
    except Exception as e:
        logger.error(f"Error adding calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/history")
async def get_history():
    """Get all calculation history"""
    try:
        history = history_repo.get_history()
        return {
            'success': True,
            'data': history
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/history/last")
async def get_last_result():
    """Get the last calculation result"""
    try:
        last_result = history_repo.get_last_result()
        return {
            'success': True,
            'data': last_result
        }
    except Exception as e:
        logger.error(f"Error retrieving last result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/history")
async def clear_history():
    """Clear all calculation history"""
    try:
        history_repo.clear_history()
        return {
            'success': True,
            'data': {'message': 'History cleared successfully'}
        }
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "history"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)