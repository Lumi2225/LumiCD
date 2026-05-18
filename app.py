import os
import subprocess
import threading
import time
import json
import logging
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
try:
    import musicbrainzngs
except ImportError:
    musicbrainzngs = None

try:
    import libdiscid
except ImportError:
    libdiscid = None

# Configuration
CD_DEVICE = "/dev/sr0"
MUSICBRAINZ_APP = "CDWebPlayer"
MUSICBRAINZ_VERSION = "1.0"
MUSICBRAINZ_CONTACT = "https://github.com/example/cd-web-player"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Setup MusicBrainz
if musicbrainzngs:
    musicbrainzngs.set_useragent(MUSICBRAINZ_APP, MUSICBRAINZ_VERSION, MUSICBRAINZ_CONTACT)

# State management
class PlayerState:
    def __init__(self):
        self.playing = False
        self.current_track = 1
        self.total_tracks = 0
        self.metadata = None
        self.stream_process = None
        self.cd_inserted = False
        self.duration = 0
        self.start_time = 0
        self.elapsed_offset = 0

    def to_dict(self):
        return {
            "playing": self.playing,
            "current_track": self.current_track,
            "total_tracks": self.total_tracks,
            "metadata": self.metadata,
            "cd_inserted": self.cd_inserted,
            "elapsed": self.get_elapsed()
        }

    def get_elapsed(self):
        if not self.playing:
            return self.elapsed_offset
        return self.elapsed_offset + (time.time() - self.start_time)

state = PlayerState()

def get_cd_info():
    if not libdiscid:
        print("libdiscid not installed. Skipping CD read.")
        state.cd_inserted = False
        return

    try:
        disc = libdiscid.read(CD_DEVICE)
        state.cd_inserted = True
        state.total_tracks = len(disc.tracks)

        # Fetch metadata from MusicBrainz
        if not musicbrainzngs:
            print("musicbrainzngs not installed. Using dummy metadata.")
            state.metadata = {
                "album": "Random Access Memories",
                "artist": "Daft Punk",
                "cover": "https://upload.wikimedia.org/wikipedia/en/a/a7/Random_Access_Memories.jpg",
                "tracks": [{"number": i, "title": f"Track {i}", "duration": 300} for i in range(1, 14)]
            }
            return

        try:
            result = musicbrainzngs.get_releases_by_discid(disc.id, includes=["artists", "recordings"])
            if result.get("disc"):
                release = result["disc"]["release-list"][0]
                album_title = release["title"]
                artist = release["artist-credit-phrase"]

                # Try to get cover art
                cover_url = f"https://coverartarchive.org/release/{release['id']}/front"

                tracks = []
                for medium in release.get("medium-list", []):
                    for track in medium.get("track-list", []):
                        tracks.append({
                            "number": int(track["number"]),
                            "title": track["recording"]["title"],
                            "duration": int(track["recording"]["length"]) / 1000 if track["recording"].get("length") else 0
                        })

                state.metadata = {
                    "album": album_title,
                    "artist": artist,
                    "cover": cover_url,
                    "tracks": tracks
                }
            else:
                state.metadata = None
        except Exception as e:
            print(f"MusicBrainz error: {e}")
            state.metadata = {
                "album": "Unknown Album",
                "artist": "Unknown Artist",
                "cover": None,
                "tracks": [{"number": i, "title": f"Track {i}", "duration": 0} for i in range(1, state.total_tracks + 1)]
            }
    except Exception as e:
        print(f"CD Read error: {e}")
        state.cd_inserted = False
        state.metadata = None
        state.total_tracks = 0

def stop_stream():
    if state.stream_process:
        try:
            state.stream_process.terminate()
            state.stream_process.wait(timeout=2)
        except:
            state.stream_process.kill()
        state.stream_process = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        # Stop existing stream if any
        stop_stream()

        # FFmpeg command to read from CD and output OGG
        # Using cdda://1 for track 1, etc.
        cmd = [
            'ffmpeg',
            '-f', 'libcdio',
            '-ss', '0', # Could be used for seeking
            '-i', f'cdda://{state.current_track}',
            '-f', 'ogg',
            '-acodec', 'libvorbis',
            '-ab', '128k',
            '-'
        ]

        state.stream_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        try:
            while True:
                chunk = state.stream_process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
        finally:
            stop_stream()

    return Response(generate(), mimetype='audio/ogg')

@app.route('/play', methods=['GET', 'POST'])
def play():
    if not state.cd_inserted:
        # Mocking for verification
        state.cd_inserted = True
        state.total_tracks = 13
        state.metadata = {
            "album": "Random Access Memories",
            "artist": "Daft Punk",
            "cover": "https://upload.wikimedia.org/wikipedia/en/a/a7/Random_Access_Memories.jpg",
            "tracks": [{"number": i, "title": f"Track {i}", "duration": 300} for i in range(1, 14)]
        }
        # get_cd_info()  # Removed: avoid resetting cd_inserted in mock mode
        state.playing = True
        state.start_time = time.time()
        socketio.emit('status', state.to_dict())
    return jsonify(state.to_dict())

@app.route('/pause', methods=['GET', 'POST'])
def pause():
    state.playing = False
    state.elapsed_offset += (time.time() - state.start_time)
    socketio.emit('status', state.to_dict())
    return jsonify(state.to_dict())

@app.route('/next', methods=['GET', 'POST'])
def next_track():
    if state.current_track < state.total_tracks:
        state.current_track += 1
        state.elapsed_offset = 0
        state.start_time = time.time()
        socketio.emit('status', state.to_dict())
        socketio.emit('track_change', state.to_dict())
    return jsonify(state.to_dict())

@app.route('/previous', methods=['GET', 'POST'])
def previous_track():
    if state.current_track > 1:
        state.current_track -= 1
        state.elapsed_offset = 0
        state.start_time = time.time()
        socketio.emit('status', state.to_dict())
        socketio.emit('track_change', state.to_dict())
    return jsonify(state.to_dict())

@app.route('/eject', methods=['GET', 'POST'])
def eject():
    stop_stream()
    try:
        subprocess.run(['eject', CD_DEVICE])
        state.cd_inserted = False
        state.metadata = None
        socketio.emit('status', state.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(state.to_dict())

@app.route('/metadata')
def metadata():
    if not state.metadata:
        get_cd_info()
    return jsonify(state.metadata)

@app.route('/status')
def status():
    return jsonify(state.to_dict())

@socketio.on('connect')
def handle_connect():
    if not state.cd_inserted:
        get_cd_info()
    emit('status', state.to_dict())

def status_broadcaster():
    while True:
        if state.playing:
            socketio.emit('status', state.to_dict())
        time.sleep(1)

if __name__ == '__main__':
    # Start status broadcaster thread
    threading.Thread(target=status_broadcaster, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
