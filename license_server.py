# license_server.py
# Flask app storing license_id -> key mapping.
from flask import Flask, request, jsonify, abort
import os
import base64
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = os.environ.get("LICENSE_DB", "licenses.db")

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS licenses(
        license_id TEXT PRIMARY KEY,
        key_b64 TEXT,
        created_at TEXT,
        meta TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

@app.route("/create_license", methods=["POST"])
def create_license():
    data = request.get_json()
    if not data or "license_id" not in data or "key_b64" not in data:
        return jsonify({"error":"license_id and key_b64 required"}), 400
    license_id = data["license_id"]
    key_b64 = data["key_b64"]
    meta = data.get("meta","")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO licenses(license_id,key_b64,created_at,meta) VALUES(?,?,?,?)",
                    (license_id, key_b64, datetime.utcnow().isoformat(), meta))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()
    return jsonify({"ok": True}), 200

@app.route("/get_key", methods=["POST"])
def get_key():
    # Expect JSON: { "license_id": "...", "license_token": "..." }
    data = request.get_json()
    if not data or "license_id" not in data or "license_token" not in data:
        return jsonify({"error":"license_id and license_token required"}), 400

    # Very minimal token check. Replace with real auth checks.
    license_token = data["license_token"]
    # Example: check against env var or DB; here, accept if token equals a server-side secret
    expected = os.environ.get("LICENSE_SERVER_SECRET")
    if expected is None or license_token != expected:
        return jsonify({"error":"invalid token"}), 403

    license_id = data["license_id"]
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT key_b64 FROM licenses WHERE license_id=?", (license_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error":"license not found"}), 404
    return jsonify({"key_b64": row[0]}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
