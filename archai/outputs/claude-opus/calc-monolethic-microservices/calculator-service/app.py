"""
Calculator Service - Microservice containing calculator business logic
"""
from flask import Flask, request, jsonify
import re
import requests
from datetime import datetime
from shared.models import CalculationResult, CalculationRequest, CalculationResponse

app = Flask(__name__)

HISTORY_SERVICE_URL = "http://history-service:5002"

class CalculatorService:
    """Service containing calculator business logic"""
    
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
    
    def calculate(self, expression: str) -> CalculationResponse:
        """Calculate the result of a mathematical expression"""
        try:
            # Clean and validate expression
            clean_expr = self._clean_expression(expression)
            if not self._is_valid_expression(clean_expr):
                return CalculationResponse(success=False, error="Invalid expression")
            
            # Handle special keywords
            if clean_expr.lower() == 'ans':
                last_result = self._get_last_result()
                if last_result is None:
                    return CalculationResponse(success=False, error="No previous calculation")
                return CalculationResponse(success=True, result=last_result)
            
            # Replace 'ans' with last result if present
            if 'ans' in clean_expr.lower():
                last_result = self._get_last_result()
                if last_result is None:
                    return CalculationResponse(success=False, error="No previous calculation for 'ans'")
                clean_expr = re.sub(r'\bans\b', str(last_result), clean_expr, flags=re.IGNORECASE)
            
            # Evaluate expression
            result = eval(clean_expr)
            
            # Save to history
            calculation = CalculationResult(
                expression=expression,
                result=result,
                timestamp=datetime.now()
            )
            self._save_to_history(calculation)
            
            return CalculationResponse(success=True, result=result)
            
        except ZeroDivisionError:
            return CalculationResponse(success=False, error="Division by zero")
        except Exception as e:
            return CalculationResponse(success=False, error=f"Calculation error: {str(e)}")
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize mathematical expression"""
        # Remove whitespace
        clean = re.sub(r'\s+', '', expression)
        # Replace ^ with ** for Python power operator
        clean = re.sub(r'\^', '**', clean)
        return clean
    
    def _is_valid_expression(self, expression: str) -> bool:
        """Validate mathematical expression for safety"""
        # Allow only numbers, operators, parentheses, decimal points, and 'ans'
        pattern = r'^[0-9+\-*/().^%\s]*$|^ans$|^.*ans.*$'
        return bool(re.match(pattern, expression, re.IGNORECASE))
    
    def _get_last_result(self) -> float:
        """Get last calculation result from history service"""
        try:
            response = requests.get(f"{HISTORY_SERVICE_URL}/history/last")
            if response.status_code == 200:
                data = response.json()
                return data.get('last_result')
            return None
        except Exception:
            return None
    
    def _save_to_history(self, calculation: CalculationResult) -> None:
        """Save calculation to history service"""
        try:
            requests.post(f"{HISTORY_SERVICE_URL}/history", json=calculation.to_dict())
        except Exception:
            pass  # Gracefully handle history service failures


calculator_service = CalculatorService()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "calculator-service"})


@app.route('/calculate', methods=['POST'])
def calculate():
    """Calculate mathematical expression"""
    try:
        data = request.json
        expression = data.get('expression', '')
        
        result = calculator_service.calculate(expression)
        return jsonify(result.to_dict())
        
    except Exception as e:
        return jsonify(CalculationResponse(success=False, error=str(e)).to_dict()), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)