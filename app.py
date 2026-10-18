import os
import re
import subprocess
import yt_dlp
from urllib.parse import quote
from flask import Flask, jsonify, request, Response, stream_with_context

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_meta():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()
    encoded_song = quote(clean_song)
    proxy_url = f"https://xiaozhi-esp32-music.onrender.com/stream_bytes?song={encoded_song}"

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
            info = ydl.extract_info(f"scsearch1:{song_name}", download=False)
            if info and "entries" in info and len(info["entries"]) > 0:
                entry = info["entries"][0]
                if entry:
                    source_url = entry.get("url")

                    if source_url:
                        # Launch FFmpeg process to decode source_url and output pure MP3 on stdout
                        ffmpeg_cmd = [
                            "ffmpeg",
                            "-i", source_url,
                            "-f", "mp3",
                            "-acodec", "libmp3lame",
                            "-ab", "128k",
                            "-ar", "44100",
                            "-ac", "2",
                            "pipe:1"
                        ]

                        process = subprocess.Popen(
                            ffmpeg_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            bufsize=10 ** 6
                        )

                        def generate_mp3():
                            try:
                                while True:
                                    chunk = process.stdout.read(4096)
                                    if not chunk:
                                        break
                                    yield chunk
                            finally:
                                process.kill()

                        return Response(
                            stream_with_context(generate_mp3()),
                            content_type="audio/mpeg"
                        )

    except Exception as e:
        print(f"Transcode Error: {str(e)}")
        return str(e), 500

    return "Song not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
