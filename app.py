from flask import Flask, jsonify, render_template, request
import os
import requests
from collections import OrderedDict

app = Flask(__name__)

# Airtable API setup
AIRTABLE_BASE_URL = os.environ.get("BASE_URL")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")  # Securely load from environment

# -------- Airtable Fetch --------
def fetch_stickers_from_airtable():
    """Fetch all stickers from Airtable."""
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {"pageSize": 100}
    stickers = []

    url = AIRTABLE_BASE_URL
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Failed to fetch data from Airtable:", response.text)
            break

        data = response.json()
        for record in data.get("records", []):
            fields = record.get("fields", {})
            sticker_name = fields.get("Sticker Name", "Unknown")
            image_link = fields.get("Sticker Image Link", "")
            artist = fields.get("Artist", "none")
            event = fields.get("Event", "none")

            stickers.append({
                "name": sticker_name,
                "picture": image_link,
                "artist": artist,
                "event": event
            })

        # Pagination
        offset = data.get("offset")
        url = f"{AIRTABLE_BASE_URL}?offset={offset}" if offset else None

    # Sort by name
    stickers.sort(key=lambda x: x["name"].lower())
    return stickers

# -------- Web Routes --------
@app.route("/")
def index():
    stickers = fetch_stickers_from_airtable()
    return render_template("index.html", stickers=stickers)

@app.route("/api/all")
def api_all():
    artist_filter = request.args.get("artist", "").lower()
    event_filter = request.args.get("program", "").lower()  # 'program' param kept for compatibility

    stickers = fetch_stickers_from_airtable()

    filtered = []
    for s in stickers:
        if artist_filter and s["artist"].lower() != artist_filter:
            continue
        if event_filter and s["event"].lower() != event_filter:
            continue

        item = OrderedDict([
            ("name", s["name"]),
            ("picture", s["picture"]),
            ("artist", s["artist"]),
            ("event", s["event"])
        ])
        filtered.append(item)

    return jsonify({"items": filtered})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=41579)
