#!/usr/bin/env python3
# spotify_cloud_server.py
import os
import requests
import json
import base64
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# .env dosyasından hassas bilgileri yükle
load_dotenv()

app = Flask(__name__)

# Spotify API bilgileri
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
RASPBERRY_PI_IP = os.getenv("RASPBERRY_PI_IP", "192.168.1.x")  # Raspberry Pi'nizin IP adresi
DEVICE_ID = os.getenv("SPOTIFY_DEVICE_ID")  # Raspotify cihaz ID'si

# Spotify API'ları için erişim jetonu alın
def get_access_token():
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Erişim jetonu alınamadı: {response.text}")
        return None

# Mevcut kullanılabilir cihazları al
@app.route("/devices", methods=["GET"])
def get_devices():
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": f"Cihazlar alınamadı: {response.text}"}), response.status_code

# Şarkı çal
@app.route("/play", methods=["POST"])
def play_track():
    data = request.json
    track_uri = data.get("track_uri")
    
    if not track_uri:
        return jsonify({"error": "track_uri parametresi gerekli"}), 400
    
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Belirli bir cihazda çalma
    endpoint = f"https://api.spotify.com/v1/me/player/play"
    if DEVICE_ID:
        endpoint += f"?device_id={DEVICE_ID}"
    
    data = {
        "uris": [track_uri]
    }
    
    response = requests.put(endpoint, headers=headers, json=data)
    
    if response.status_code in [200, 204]:
        return jsonify({"success": True, "message": "Şarkı başarıyla çalınıyor"})
    else:
        return jsonify({"error": f"Şarkı çalınamadı: {response.text}"}), response.status_code

# Şarkı ara
@app.route("/search", methods=["GET"])
def search_tracks():
    query = request.args.get("q")
    
    if not query:
        return jsonify({"error": "q parametresi gerekli"}), 400
    
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "q": query,
        "type": "track",
        "limit": 10
    }
    
    response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": f"Arama yapılamadı: {response.text}"}), response.status_code

# Şu anda çalan şarkıyı durdur
@app.route("/pause", methods=["POST"])
def pause_playback():
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoint = "https://api.spotify.com/v1/me/player/pause"
    if DEVICE_ID:
        endpoint += f"?device_id={DEVICE_ID}"
    
    response = requests.put(endpoint, headers=headers)
    
    if response.status_code in [200, 204]:
        return jsonify({"success": True, "message": "Çalma duraklatıldı"})
    else:
        return jsonify({"error": f"Çalma duraklatılamadı: {response.text}"}), response.status_code

# Şu anda çalan şarkıyı devam ettir
@app.route("/resume", methods=["POST"])
def resume_playback():
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoint = "https://api.spotify.com/v1/me/player/play"
    if DEVICE_ID:
        endpoint += f"?device_id={DEVICE_ID}"
    
    response = requests.put(endpoint, headers=headers)
    
    if response.status_code in [200, 204]:
        return jsonify({"success": True, "message": "Çalma devam ediyor"})
    else:
        return jsonify({"error": f"Çalma devam ettirilemedi: {response.text}"}), response.status_code

# Şu anda çalan şarkı bilgisini al
@app.route("/now-playing", methods=["GET"])
def get_now_playing():
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())
    elif response.status_code == 204:
        return jsonify({"message": "Şu anda hiçbir şey çalmıyor"})
    else:
        return jsonify({"error": f"Çalan şarkı bilgisi alınamadı: {response.text}"}), response.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)