from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = "test-simple-app-key"

# Apply ProxyFix with all options
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1,
    x_port=1
)

@app.route('/')
def hello():
    return "Hello from Simple Flask App!"

@app.route('/api/ping')
def ping():
    return jsonify({
        'status': 'ok',
        'message': 'pong'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)