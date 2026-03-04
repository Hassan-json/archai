"""
History Service - Microservice for managing calculation history
"""
from flask import Flask, request, jsonify
from datetime import datetime
from repository import HistoryRepository
from shared.models import CalculationResult

app = Flask(__name__)
history_repo = HistoryRepository()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "history-service"})


@app.route('/history', methods=['POST'])
def save_calculation():
    """Save a calculation to history"""
    try:
        data = request.json
        calculation = CalculationResult(
            expression=data['expression'],
            result=data['result'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )
        history_repo.save_calculation(calculation)
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/history', methods=['GET'])
def get_history():
    """Get all calculation history"""
    try:
        history = history_repo.get_history()
        return jsonify({
            "success": True,
            "history": [calc.to_dict() for calc in history]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/history', methods=['DELETE'])
def clear_history():
    """Clear all calculation history"""
    try:
        history_repo.clear_history()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/history/last', methods=['GET'])
def get_last_result():
    """Get the last calculation result"""
    try:
        last_result = history_repo.get_last_result()
        return jsonify({
            "success": True,
            "last_result": last_result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)