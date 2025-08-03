# This code is entirely made by AI, and as such no license or usage restrictions is placed on it.


from flask import Flask, jsonify, render_template, send_from_directory, request
import os
import json
import requests
from pathlib import Path
from collections import OrderedDict

app = Flask(__name__)

# Constants
STICKERS_FOLDER = os.path.join('static', 'stickers')
BASE_URL = 'https://stickers.dld.hackclub.app'
REPO = "danieliscrazy/stickerdb"
GITHUB_API_BASE = f"https://api.github.com/repos/{REPO}/contents"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"
ARTISTS_FILE = 'artists.json'
PROGRAMS_FILE = 'programs.json'

# -------- GitHub Sticker Sync --------
def download_missing_stickers():
    """Check GitHub and download missing PNG/SVG stickers to local folder."""
    response = requests.get(f"{GITHUB_API_BASE}/static/stickers")
    if response.status_code != 200:
        print("Failed to fetch sticker list from GitHub.")
        return

    files = response.json()
    os.makedirs(STICKERS_FOLDER, exist_ok=True)
    existing_files = set(os.listdir(STICKERS_FOLDER))

    for file in files:
        name = file["name"]
        if name.lower().endswith(('.png', '.svg')) and name not in existing_files:
            print(f"Downloading: {name}")
            download_url = file["download_url"]
            local_path = Path(STICKERS_FOLDER) / name
            img_data = requests.get(download_url).content
            with open(local_path, 'wb') as f:
                f.write(img_data)

# -------- GitHub Metadata Sync --------
def fetch_and_update_json(filename):
    """Compare local JSON file with GitHub version, update if different."""
    url = f"{RAW_BASE}/{filename}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Could not fetch {filename} from GitHub.")
            return
        remote_json = response.json()
    except Exception as e:
        print(f"Failed to load remote {filename}: {e}")
        return

    # Load local JSON if it exists
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                local_json = json.load(f)
            except:
                local_json = {}
    else:
        local_json = {}

    # Compare and update if different
    if local_json != remote_json:
        with open(filename, 'w') as f:
            json.dump(remote_json, f, indent=2)
        print(f"Updated {filename} from GitHub.")
    else:
        print(f"{filename} is already up to date.")

# Run all sync operations at startup
download_missing_stickers()
fetch_and_update_json(ARTISTS_FILE)
fetch_and_update_json(PROGRAMS_FILE)

# -------- Metadata Lookup --------
def load_mapping(filename):
    """Load mapping file (artists or programs), return sticker → key dict."""
    if not os.path.exists(filename):
        return {}

    with open(filename, 'r') as f:
        raw = json.load(f)

    result = {}
    for key, files in raw.items():
        for fname in files:
            result[fname] = key
    return result

# -------- Web Routes --------
@app.route("/")
def index():
    artist_lookup = load_mapping(ARTISTS_FILE)
    program_lookup = load_mapping(PROGRAMS_FILE)

    stickers = []
    for filename in os.listdir(STICKERS_FOLDER):
        if filename.lower().endswith(('.png', '.svg')):
            name = os.path.splitext(filename)[0]
            stickers.append({
                'name': name,
                'file': filename,
                'artist': artist_lookup.get(filename, "none"),
                'program': program_lookup.get(filename, "none")
            })
    stickers.sort(key=lambda x: x['name'].lower())
    return render_template("index.html", stickers=stickers)

@app.route("/api/all")
def api_all():
    artist_filter = request.args.get("artist", "").lower()
    program_filter = request.args.get("program", "").lower()

    artist_lookup = load_mapping(ARTISTS_FILE)
    program_lookup = load_mapping(PROGRAMS_FILE)

    items = []
    for filename in os.listdir(STICKERS_FOLDER):
        if filename.lower().endswith(('.png', '.svg')):
            name, ext = os.path.splitext(filename)
            artist = artist_lookup.get(filename, "none")
            program = program_lookup.get(filename, "none")

            if artist_filter and artist.lower() != artist_filter:
                continue
            if program_filter and program.lower() != program_filter:
                continue

            item = OrderedDict([
                ("name", name),
                ("picture", f"{BASE_URL}/static/stickers/{filename}"),
                ("event", program),
                ("artist", artist)
            ])
            items.append(item)

    # Sort by name
    items.sort(key=lambda x: x["name"].lower())
    return jsonify({"items": items})

@app.route("/stickers/<path:filename>")
def sticker_file(filename):
    return send_from_directory(STICKERS_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=41579)
