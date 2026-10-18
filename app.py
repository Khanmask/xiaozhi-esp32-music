import os
import re
import sys
import logging
import subprocess
import yt_dlp
import imageio_ffmpeg
from urllib.parse import quote
from flask import Flask, jsonify, request, Response, stream_with_context

# Configure logging for Render
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load FFmpeg binary and grant execute permissions
try:
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    os.chmod(FFMPEG_PATH, 0o755)
    logger.info(f"FFmpeg loaded successfully at: {FFMPEG_PATH}")
except Exception as e:
    logger.error(f"Failed to set up imageio-ffmpeg: {e}")
    FFMPEG_PATH = "ffmpeg"

@app.route("/stream_pcm", methods=["GET"])
def stream_meta():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()
    encoded_song = quote(clean_song)
    proxy_url = f"https://xiaozhi-esp32-music.onrender.com/stream_bytes?song={encoded_song}"

    logger.info(f"Metadata requested for song: {clean_song}")
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

    logger.info(f"Streaming request received for song: {song_name}")

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
            # Search SoundCloud for the song requested by user
            info = ydl.extract_info(f"scsearch1:{song_name}", download=False)
            if info and "entries" in info and len(info["entries"]) > 0:
                entry = info["entries"][0]
                if entry:
                    source_url = entry.get("url")
                    title = entry.get("title", song_name)
                    logger.info(f"Found SoundCloud track: {title} | Source URL: {source_url}")

                    if source_url:
                        ffmpeg_cmd = [
                            FFMPEG_PATH,
                            "-reconnect", "1",
                            "-reconnect_streamed", "1",
                            "-reconnect_delay_max", "5",
                            "-i", source_url,
                            "-f", "mp3",
                            "-acodec", "mp3",
                            "-ab", "128k",
                            "-ar", "44100",
                            "-ac", "2",
                            "pipe:1"
                        ]

                        process = subprocess.Popen(
                            ffmpeg_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            bufsize=10 ** 6
                        )

                        def generate_mp3():
                            try:
                                while True:
                                    chunk = process.stdout.read(1024)
                                    if not chunk:
                                        err = process.stderr.read().decode('utf-8', errors='ignore')
                                        if err:
                                            logger.error(f"FFmpeg Stderr: {err}")
                                        break
                                    yield chunk
                            finally:
                                process.kill()
                                logger.info("FFmpeg transcode stream closed.")

                        return Response(
                            stream_with_context(generate_mp3()),
                            content_type="audio/mpeg",
                            headers={
                                "Accept-Ranges": "bytes",
                                "Cache-Control": "no-cache"
                            }
                        )

    except Exception as e:
        logger.error(f"Transcoding Error: {str(e)}")
        return str(e), 500

    return "Song not found on SoundCloud", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
