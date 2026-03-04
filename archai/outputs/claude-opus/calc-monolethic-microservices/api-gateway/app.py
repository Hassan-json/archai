"""
API Gateway - Routes requests to appropriate microservices
"""
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Service endpoints
CALCULATOR_SERVICE_URL = "http://calculator-service:5001"
HISTORY_SERVICE_URL = "http://history-service:5002"
PRESENTATION_SERVICE_URL = "http://presentation-service:5003"


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "api-gateway"})


@app.route('/services/health', methods=['GET'])
def check_all_services():
    """Check health of all microservices"""
    services = {
        "calculator": CALCULATOR_SERVICE_URL,
        "history": HISTORY_SERVICE_URL,
        "presentation": PRESENTATION_SERVICE_URL
    }
    
    health_status = {}
    for service_name, service_url in services.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            health_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return jsonify(health_status)


@app.route('/calculate', methods=['POST'])
def calculate():
    """Route calculation requests to calculator service"""
    try:
        response = requests.post(
            f"{CALCULATOR_SERVICE_URL}/calculate",
            json=request.json,
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Calculator service unavailable: {str(e)}"
        }), 503


@app.route('/history', methods=['GET'])
def get_history():
    """Route history requests to history service"""
    try:
        response = requests.get(f"{HISTORY_SERVICE_URL}/history", timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"History service unavailable: {str(e)}"
        }), 503


@app.route('/history', methods=['DELETE'])
def clear_history():
    """Route history clear requests to history service"""
    try:
        response = requests.delete(f"{HISTORY_SERVICE_URL}/history", timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"History service unavailable: {str(e)}"
        }), 503


@app.route('/history/last', methods=['GET'])
def get_last_result():
    """Route last result requests to history service"""
    try:
        response = requests.get(f"{HISTORY_SERVICE_URL}/history/last", timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"History service unavailable: {str(e)}"
        }), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)