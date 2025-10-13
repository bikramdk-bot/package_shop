from flask import Flask, request, jsonify
from lookup import search_parcel, insert_parcel

app = Flask(__name__)

# ---------------------- LOOKUP ----------------------
@app.route("/lookup", methods=["GET", "POST"])
def lookup_parcel():
    """
    Customer tablet sends either:
    POST JSON: {"provider": "PostNord", "digits": "1234"}
    or
    GET params: /lookup?provider=PostNord&digits=1234
    """
    if request.method == "GET":
        provider = request.args.get("provider")
        digits = request.args.get("digits")
    else:
        data = request.get_json(force=True)
        provider = data.get("provider")
        digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    results = search_parcel(provider, digits)
    return jsonify({"results": results})


# ---------------------- INSERT ----------------------
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

# ---------------------- UPDATE STATUS ----------------------
@app.route("/update_status", methods=["POST"])
def update_status_api():
    """
    Staff marks parcel as collected, held, etc.
    Example:
    {"provider": "PostNord", "digits": "7890", "status": "collected"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")
    new_status = data.get("status")

    if not provider or not digits or not new_status:
        return jsonify({"error": "Missing provider, digits, or status"}), 400

    from lookup import update_status
    result = update_status(provider, digits, new_status)
    return jsonify(result)


# ---------------------- DELETE PARCEL ----------------------
@app.route("/delete_parcel", methods=["POST"])
def delete_parcel_api():
    """
    Staff manually deletes a parcel record.
    Example:
    {"provider": "PostNord", "digits": "7890"}
    """
    data = request.get_json(force=True)
    provider = data.get("provider")
    digits = data.get("digits")

    if not provider or not digits:
        return jsonify({"error": "Missing provider or digits"}), 400

    from lookup import delete_parcel
    result = delete_parcel(provider, digits)
    return jsonify(result)


# ---------------------- HEALTH ----------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
