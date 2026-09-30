import os
from flask import Flask, jsonify, request

app = Flask(__name__)

MODEL_VERSION = "model-8"
APPLICATION_VERSION = os.getenv("APPLICATION_VERSION", "0.0.0")
GIT_COMMIT = os.getenv("GIT_COMMIT", "local")

@app.route("/")
def home():
    return jsonify({
        "service": "mlops-demo",
        "status": "running"
    })

@app.route("/health")
def health():
    return jsonify({
        "application_version": APPLICATION_VERSION,
        "model_version": MODEL_VERSION,
        "git_commit": GIT_COMMIT,
        "status": "healthy"
    })

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    value = float(data["value"])

    prediction = value * 2

    return jsonify({
        "input": value,
        "prediction": prediction,
        "model_version": MODEL_VERSION
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)