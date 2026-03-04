from flask import Flask, jsonify
import requests

app = Flask(__name__)

HELLO_SERVICE_URL = 'http://hello_service:5001/hello'

@app.route('/hello', methods=['GET'])
def hello():
    response = requests.get(HELLO_SERVICE_URL)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)