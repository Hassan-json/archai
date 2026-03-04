"""
Calculator Service - Business Logic Microservice
Handles mathematical calculations and expression parsing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re
import requests
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Calculator Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
HISTORY_SERVICE_URL = os.getenv("HISTORY_SERVICE_URL", "http://history-service:8002")

class CalculatorEngine:
    """Core calculation engine"""
    
    def __init__(self):
        self._operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y,
            '**': lambda x, y: x ** y,
            '%': lambda x, y: x % y
        }
    
    def calculate(self, expression: str) -> float:
        """Calculate mathematical expression"""
        try:
            # Clean and validate expression
            cleaned_expr = self._clean_expression(expression)
            
            # Handle special cases
            if cleaned_expr.lower() == 'ans':
                return self._get_last_result()
            
            # Evaluate expression
            result = self._evaluate_expression(cleaned_expr)
            
            # Save to history
            self._save_to_history(expression, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Calculation error: {str(e)}")
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and validate mathematical expression"""
        # Remove spaces
        cleaned = expression.replace(' ', '')
        
        # Replace ^ with ** for Python
        cleaned = cleaned.replace('^', '**')
        
        # Validate characters
        if not re.match(r'^[0-9+\-*/.()%^]+$', cleaned.replace('**', '^')):
            raise ValueError("Invalid characters in expression")
        
        return cleaned
    
    def _evaluate_expression(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        # Using eval with restricted namespace for safety
        allowed_names = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "pow": pow
        }
        
        try:
            result = eval(expression, allowed_names)
            return float(result)
        except ZeroDivisionError:
            raise ValueError("Division by zero")
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def _get_last_result(self) -> float:
        """Get last result from history service"""
        try:
            response = requests.get(f"{HISTORY_SERVICE_URL}/history/last", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['data']:
                    return data['data']['result']
            return 0.0
        except Exception as e:
            logger.warning(f"Could not fetch last result: {str(e)}")
            return 0.0
    
    def _save_to_history(self, expression: str, result: float):
        """Save calculation to history service"""
        try:
            payload = {
                'expression': expression,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            requests.post(f"{HISTORY_SERVICE_URL}/history", json=payload, timeout=5)
        except Exception as e:
            logger.warning(f"Could not save to history: {str(e)}")

# Initialize calculator engine
calculator = CalculatorEngine()

@app.post("/calculate")
async def calculate(request: dict):
    """Calculate mathematical expression"""
    try:
        expression = request.get('expression')
        if not expression:
            raise HTTPException(status_code=400, detail="Expression is required")
        
        result = calculator.calculate(expression)
        
        return {
            'success': True,
            'data': {
                'expression': expression,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "calculator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)