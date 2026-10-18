import os
import base64
import yt_dlp
from flask import Flask, redirect, request

app = Flask(__name__)

COOKIE_PATH = "/tmp/cookies.txt"
cookies_base64 = os.environ.get("YT_COOKIES_BASE64")

if cookies_base64:
    try:
        # Decode base64 to bytes, then decode to text while ignoring invalid bytes
        cookie_bytes = base64.b64decode(cookies_base64)
        cookie_text = cookie_bytes.decode("utf-8", errors="ignore")
        
        with open(COOKIE_PATH, "w", encoding="utf-8") as f:
            f.write(cookie_text)
    except Exception as e:
        print(f"Failed to setup cookies: {e}")

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch1",
        "cookiefile": COOKIE_PATH if os.path.exists(COOKIE_PATH) and os.path.getsize(COOKIE_PATH) > 0 else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=False)
            if "entries" in info and len(info["entries"]) > 0:
                direct_audio_url = info["entries"][0]["url"]
                return redirect(direct_audio_url, code=302)
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Song not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
