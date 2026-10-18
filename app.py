import os
import re
import sys
import logging
import subprocess
import yt_dlp
import imageio_ffmpeg
from urllib.parse import quote
from flask import Flask, jsonify, request, Response, stream_with_context

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

try:
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    os.chmod(FFMPEG_PATH, 0o755)
    logger.info(f"FFmpeg binary executable set at: {FFMPEG_PATH}")
except Exception as e:
    logger.error(f"Failed to load imageio-ffmpeg: {e}")
    FFMPEG_PATH = "ffmpeg"

@app.route("/stream_pcm", methods=["GET"])
def stream_meta():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()
    encoded_song = quote(clean_song)
    proxy_url = f"https://xiaozhi-esp32-music.onrender.com/stream_bytes?song={encoded_song}"

    logger.info(f"Metadata requested for: {clean_song}")
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

    logger.info(f"Streaming request for: {song_name}")

    # Directly run yt-dlp to pipe stdout into ffmpeg for seamless transcoding
    yt_cmd = [
        "yt-dlp",
        "-f", "bestaudio/best",
        "scsearch1:" + song_name,
        "-o", "-",
        "--quiet",
        "--no-playlist"
    ]

    ffmpeg_cmd = [
        FFMPEG_PATH,
        "-i", "pipe:0",
        "-f", "mp3",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        "-ar", "44100",
        "-ac", "2",
        "pipe:1"
    ]

    try:
        logger.info(f"Piping yt-dlp output to FFmpeg for '{song_name}'...")
        yt_process = subprocess.Popen(yt_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=yt_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10 ** 6
        )

        def generate_mp3():
            try:
                while True:
                    chunk = ffmpeg_process.stdout.read(1024)
                    if not chunk:
                        err = ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                        if err:
                            logger.error(f"FFmpeg Stderr: {err}")
                        break
                    yield chunk
            finally:
                yt_process.kill()
                ffmpeg_process.kill()
                logger.info("Transcode process terminated successfully.")

        return Response(
            stream_with_context(generate_mp3()),
            content_type="audio/mpeg",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        logger.error(f"Piping Transcode Error: {str(e)}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
