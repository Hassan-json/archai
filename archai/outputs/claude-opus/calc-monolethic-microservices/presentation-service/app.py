"""
Presentation Service - CLI interface microservice
"""
from flask import Flask
import threading
from cli import CalculatorCLI

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "presentation-service"}


def run_cli():
    """Run the CLI in a separate thread"""
    cli = CalculatorCLI()
    cli.run()


if __name__ == '__main__':
    # Start CLI in background thread
    cli_thread = threading.Thread(target=run_cli, daemon=True)
    cli_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5003, debug=True)