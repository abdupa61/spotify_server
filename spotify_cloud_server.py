import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

class SpotifyController:
    """
    Render.com üzerinde Spotify API kullanarak şarkı çalma ve kontrol etme sınıfı.
    """

    def __init__(self):
        """
        SpotifyController sınıfının başlatıcı metodu.
        Environment variables'dan değerleri alır.
        """
        # Environment variables'dan değerleri al
        client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.environ.get('SPOTIFY_REDIRECT_URI')
        username = os.environ.get('SPOTIFY_USERNAME')
        
        # Değerlerin varlığını kontrol et
        if not all([client_id, client_secret, redirect_uri, username]):
            raise ValueError("Spotify environment variables (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, SPOTIFY_USERNAME) tanımlanmalı!")

        self.username = username

        # Spotify API için yetkilendirme kapsamları
        scope = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing"

        # Spotify API bağlantısını oluşturma
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            username=username
        ))

        print("Spotify Controller başlatıldı.")

    def search_track(self, query, limit=5):
        """
        Bir şarkıyı Spotify'da arar.

        Args:
            query (str): Aranacak şarkı adı veya sanatçı
            limit (int): Döndürülecek sonuç sayısı

        Returns:
            list: Bulunan şarkıların listesi (şarkı adı, sanatçı, URI)
        """
        try:
            results = self.sp.search(q=query, limit=limit, type='track')
            tracks = results['tracks']['items']

            if not tracks:
                print(f"'{query}' için şarkı bulunamadı.")
                return []

            found_tracks = []
            for i, track in enumerate(tracks):
                track_info = {
                    'index': i + 1,
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'uri': track['uri'],
                    'duration_ms': track['duration_ms']
                }
                found_tracks.append(track_info)
                print(f"{i + 1}. {track['name']} - {track['artists'][0]['name']}")

            return found_tracks

        except Exception as e:
            print(f"Şarkı arama hatası: {e}")
            return []

    def play_track(self, track_uri=None):
        """
        Seçilen şarkıyı çalar.

        Args:
            track_uri (str): Çalınacak şarkının Spotify URI'si
        """
        try:
            # Aktif cihazları kontrol etme
            devices = self.sp.devices()
            if not devices['devices']:
                print("Aktif Spotify cihazı bulunamadı. Lütfen bir cihazda Spotify'ı açın.")
                return False

            # İlk aktif cihazı kullanma
            device_id = devices['devices'][0]['id']

            if track_uri:
                self.sp.start_playback(device_id=device_id, uris=[track_uri])
                current_track = self.sp.currently_playing()
                if current_track and current_track['item']:
                    print(
                        f"Şimdi çalıyor: {current_track['item']['name']} - {current_track['item']['artists'][0]['name']}")
                return True
            else:
                print("Çalınacak şarkı seçilmedi.")
                return False

        except Exception as e:
            print(f"Şarkı çalma hatası: {e}")
            return False

    def pause(self):
        """Çalmakta olan şarkıyı duraklatır."""
        try:
            self.sp.pause_playback()
            print("Müzik duraklatıldı.")
            return True
        except Exception as e:
            print(f"Duraklatma hatası: {e}")
            return False

    def resume(self):
        """Duraklatılmış şarkıyı devam ettirir."""
        try:
            self.sp.start_playback()
            print("Müzik devam ediyor.")
            return True
        except Exception as e:
            print(f"Devam ettirme hatası: {e}")
            return False

    def next_track(self):
        """Sonraki şarkıya geçer."""
        try:
            self.sp.next_track()
            time.sleep(0.5)  # API güncellemesi için kısa bekleme
            current_track = self.sp.currently_playing()
            if current_track and current_track['item']:
                print(f"Sonraki şarkı: {current_track['item']['name']} - {current_track['item']['artists'][0]['name']}")
            return True
        except Exception as e:
            print(f"Sonraki şarkıya geçme hatası: {e}")
            return False

    def previous_track(self):
        """Önceki şarkıya geçer."""
        try:
            self.sp.previous_track()
            time.sleep(0.5)  # API güncellemesi için kısa bekleme
            current_track = self.sp.currently_playing()
            if current_track and current_track['item']:
                print(f"Önceki şarkı: {current_track['item']['name']} - {current_track['item']['artists'][0]['name']}")
            return True
        except Exception as e:
            print(f"Önceki şarkıya geçme hatası: {e}")
            return False

    def get_currently_playing(self):
        """
        Şu anda çalan şarkı bilgisini getirir.

        Returns:
            dict: Çalan şarkı bilgisi veya None
        """
        try:
            current = self.sp.currently_playing()
            if current and current['item']:
                track_info = {
                    'name': current['item']['name'],
                    'artist': current['item']['artists'][0]['name'],
                    'album': current['item']['album']['name'],
                    'progress_ms': current['progress_ms'],
                    'duration_ms': current['item']['duration_ms']
                }
                print(f"Şu anda çalıyor: {track_info['name']} - {track_info['artist']}")
                return track_info
            else:
                print("Şu anda çalan şarkı yok.")
                return None
        except Exception as e:
            print(f"Çalan şarkı bilgisi hatası: {e}")
            return None

# Global SpotifyController instance
spotify_controller = SpotifyController()

# API Endpoints
@app.route('/search', methods=['POST'])
def search_track():
    """Şarkı arama endpoint"""
    data = request.get_json()
    query = data.get('query')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({'error': 'Query parametresi gerekli'}), 400
    
    tracks = spotify_controller.search_track(query, limit)
    return jsonify({'tracks': tracks})

@app.route('/play', methods=['POST'])
def play_track():
    """Şarkı çalma endpoint"""
    data = request.get_json()
    track_uri = data.get('track_uri')
    
    success = spotify_controller.play_track(track_uri)
    if success:
        return jsonify({'message': 'Şarkı çalmaya başladı'})
    else:
        return jsonify({'error': 'Şarkı çalınamadı'}), 400

@app.route('/pause', methods=['POST'])
def pause_track():
    """Şarkı duraklat endpoint"""
    success = spotify_controller.pause()
    if success:
        return jsonify({'message': 'Müzik duraklatıldı'})
    else:
        return jsonify({'error': 'Müzik duraklatılamadı'}), 400

@app.route('/resume', methods=['POST'])
def resume_track():
    """Şarkı devam ettir endpoint"""
    success = spotify_controller.resume()
    if success:
        return jsonify({'message': 'Müzik devam ediyor'})
    else:
        return jsonify({'error': 'Müzik devam ettirilemedi'}), 400

@app.route('/next', methods=['POST'])
def next_track():
    """Sonraki şarkı endpoint"""
    success = spotify_controller.next_track()
    if success:
        return jsonify({'message': 'Sonraki şarkıya geçildi'})
    else:
        return jsonify({'error': 'Sonraki şarkıya geçilemedi'}), 400

@app.route('/previous', methods=['POST'])
def previous_track():
    """Önceki şarkı endpoint"""
    success = spotify_controller.previous_track()
    if success:
        return jsonify({'message': 'Önceki şarkıya geçildi'})
    else:
        return jsonify({'error': 'Önceki şarkıya geçilemedi'}), 400

@app.route('/current', methods=['GET'])
def current_track():
    """Şu anki şarkı endpoint"""
    track_info = spotify_controller.get_currently_playing()
    if track_info:
        return jsonify({'current_track': track_info})
    else:
        return jsonify({'message': 'Şu anda çalan şarkı yok'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'message': 'Spotify Controller çalışıyor'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
