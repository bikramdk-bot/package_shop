from flask import Flask, request, jsonify
from lookup import search_parcel, insert_parcel

app = Flask(__name__)

@app.route("/lookup", methods=["POST"])
def lookup_parcel():
    """
    Customer tablet sends JSON:
    {"provider": "PostNord", "digits": "1234"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    results = search_parcel(provider, digits)
    return jsonify({"results": results})


@app.route("/insert", methods=["POST"])
def insert_parcel_api():
    """
    For manual add or future scanner API call:
    {"provider": "DAO", "digits": "5678"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    insert_parcel(provider, digits)
    return jsonify({"status": "inserted", "provider": provider, "digits": digits})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
