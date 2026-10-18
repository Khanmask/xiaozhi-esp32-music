import os
import re
import yt_dlp
import requests
from flask import Flask, jsonify, request, Response, stream_with_context

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_meta():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    # Clean up speech-to-text artifacts
    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()

    # Point the audio_url to our proxy endpoint on Render
    proxy_url = f"https://xiaozhi-esp32-music.onrender.com/stream_bytes?song={clean_song}"

    return jsonify({
        "audio_url": proxy_url,
        "title": clean_song,
        "artist": "SoundCloud",
        "lyric_url": ""
    })

@app.route("/stream_bytes", methods=["GET"])
def stream_bytes():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "default_search": "scsearch1",
        "nocheckcertificate": True,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = yt_dlp.YoutubeDL(ydl_opts).extract_info(f"scsearch1:{song_name}", download=False)
            if info and "entries" in info and len(info["entries"]) > 0:
                entry = info["entries"][0]
                if entry:
                    stream_url = entry.get("url")
                    
                    # Look for a direct non-m3u8 audio format if available in formats
                    if "formats" in entry:
                        for fmt in entry["formats"]:
                            if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none":
                                proto = fmt.get("protocol", "")
                                if "m3u8" not in proto and "http" in proto:
                                    stream_url = fmt.get("url")
                                    break

                    if stream_url:
                        # Proxy the audio stream directly to the ESP32
                        req = requests.get(stream_url, stream=True, timeout=15)
                        return Response(
                            stream_with_context(req.iter_content(chunk_size=4096)),
                            content_type=req.headers.get("content-type", "audio/mpeg")
                        )
                        
    except Exception as e:
        print(f"Proxy Error: {str(e)}")
        return str(e), 500

    return "Song not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
