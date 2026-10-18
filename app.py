import os
import re
import sys
import logging
import requests
from urllib.parse import quote
from flask import Flask, jsonify, request, Response, stream_with_context

# Configure logging so Render captures everything natively
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_meta():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()
    encoded_song = quote(clean_song)
    proxy_url = f"https://xiaozhi-esp32-music.onrender.com/stream_bytes?song={encoded_song}"

    logger.info(f"Meta requested for: {clean_song}")
    return jsonify({
        "audio_url": proxy_url,
        "title": clean_song,
        "artist": "SoundHelix Test",
        "lyric_url": ""
    })

@app.route("/stream_bytes", methods=["GET"])
def stream_bytes():
    song_name = request.args.get("song", "")
    logger.info(f"Streaming bytes requested for: {song_name} (Using direct static test MP3)")

    try:
        # Bypassing yt-dlp & ffmpeg temporarily to test raw audio buffer consumption
        test_mp3_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        r = requests.get(test_mp3_url, stream=True)
        
        return Response(
            stream_with_context(r.iter_content(chunk_size=4096)),
            content_type="audio/mpeg"
        )
    except Exception as e:
        logger.error(f"Static Stream Error: {str(e)}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
