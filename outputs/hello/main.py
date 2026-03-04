from flask import Flask, jsonify

app = Flask(__name__)

class HelloWorldService:
    def get_message(self):
        return "Hello, World!"

@app.route('/hello', methods=['GET'])
def hello():
    service = HelloWorldService()
    message = service.get_message()
    return jsonify({"message": message})

if __name__ == '__main__':
    app.run(debug=True)