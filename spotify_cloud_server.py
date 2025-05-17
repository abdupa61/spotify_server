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
DEVICE_ID = os.getenv("SPOTIFY_DEVICE_ID")  # Raspotify cihaz ID'si

# Spotify API'ları için erişim jetonu alın
def get_access_token():
    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        print("Eksik Spotify API bilgileri")
        return None
        
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
    
    try:
        response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Erişim jetonu alınamadı: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Token alma hatası: {e}")
        return None

# Health check endpoint
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "Spotify Cloud Server çalışıyor"})

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
    
    try:
        response = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Cihazlar alınamadı: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

# Şarkı çal
@app.route("/play", methods=["POST"])
def play_track():
    # JSON verisi kontrol
    if not request.is_json:
        return jsonify({"error": "Content-Type application/json olmalı"}), 400
        
    data = request.json
    track_uri = data.get("track_uri") if data else None
    
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
    endpoint = "https://api.spotify.com/v1/me/player/play"
    if DEVICE_ID:
        endpoint += f"?device_id={DEVICE_ID}"
    
    payload = {
        "uris": [track_uri]
    }
    
    try:
        response = requests.put(endpoint, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            return jsonify({"success": True, "message": "Şarkı başarıyla çalınıyor"})
        else:
            return jsonify({"error": f"Şarkı çalınamadı: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

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
    
    try:
        response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Arama yapılamadı: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

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
    
    try:
        response = requests.put(endpoint, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            return jsonify({"success": True, "message": "Çalma duraklatıldı"})
        else:
            return jsonify({"error": f"Çalma duraklatılamadı: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

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
    
    try:
        response = requests.put(endpoint, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            return jsonify({"success": True, "message": "Çalma devam ediyor"})
        else:
            return jsonify({"error": f"Çalma devam ettirilemedi: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

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
    
    try:
        response = requests.get("https://api.spotify.com/v1/me/player", headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        elif response.status_code == 204:
            return jsonify({"message": "Şu anda hiçbir şey çalmıyor"})
        else:
            return jsonify({"error": f"Çalan şarkı bilgisi alınamadı: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

# Ses seviyesi ayarlama
@app.route("/volume", methods=["POST"])
def set_volume():
    if not request.is_json:
        return jsonify({"error": "Content-Type application/json olmalı"}), 400
        
    data = request.json
    volume = data.get("volume") if data else None
    
    if volume is None or not isinstance(volume, int) or not (0 <= volume <= 100):
        return jsonify({"error": "volume parametresi 0-100 arası integer olmalı"}), 400
    
    access_token = get_access_token()
    
    if not access_token:
        return jsonify({"error": "Erişim jetonu alınamadı"}), 401
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"https://api.spotify.com/v1/me/player/volume?volume_percent={volume}"
    if DEVICE_ID:
        endpoint += f"&device_id={DEVICE_ID}"
    
    try:
        response = requests.put(endpoint, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            return jsonify({"success": True, "message": f"Ses seviyesi {volume}% olarak ayarlandı"})
        else:
            return jsonify({"error": f"Ses seviyesi ayarlanamadı: {response.status_code} - {response.text}"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"İstek hatası: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)