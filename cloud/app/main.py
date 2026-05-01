from __future__ import annotations

from flask import Flask, jsonify, request

from shared.schemas import DeviceHeartbeat, DeviceRegistrationRequest, DeviceRegistrationResponse


app = Flask(__name__)


@app.route("/control/health", methods=["GET"])
def control_health():
    return jsonify({
        "status": "ok",
        "service": "package-shop-control-plane",
    })


@app.route("/device/register", methods=["POST"])
def register_device():
    try:
        payload = request.get_json(force=True) or {}
        registration = DeviceRegistrationRequest.from_dict(payload)
        response = DeviceRegistrationResponse.issue()
        return jsonify({
            "request": registration.to_dict(),
            "registration": response.to_dict(),
        }), 201
    except ValueError as exc:
        return jsonify({"error": "invalid_registration", "detail": str(exc)}), 400


@app.route("/device/heartbeat", methods=["POST"])
def device_heartbeat():
    try:
        payload = request.get_json(force=True) or {}
        heartbeat = DeviceHeartbeat.from_dict(payload)
        return jsonify({
            "received": True,
            "heartbeat": heartbeat.to_dict(),
        })
    except ValueError as exc:
        return jsonify({"error": "invalid_heartbeat", "detail": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)