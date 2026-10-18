import os
import base64
import re
import yt_dlp
from ytmusicapi import YTMusic
from flask import Flask, redirect, request

app = Flask(__name__)
ytmusic = YTMusic()

COOKIE_PATH = "/tmp/cookies.txt"
cookies_base64 = os.environ.get("YT_COOKIES_BASE64")

if cookies_base64:
    try:
        cookies_base64 = "".join(cookies_base64.split()).strip('"\'')
        cookies_base64 = re.sub(r'[^A-Za-z0-9+/=]', '', cookies_base64)
        missing_padding = len(cookies_base64) % 4
        if missing_padding:
            cookies_base64 += '=' * (4 - missing_padding)

        cookie_bytes = base64.b64decode(cookies_base64)
        cookie_text = cookie_bytes.decode("utf-8", errors="ignore")
        
        with open(COOKIE_PATH, "w", encoding="utf-8") as f:
            f.write(cookie_text)
        print("Cookies successfully written to /tmp/cookies.txt")
    except Exception as e:
        print(f"Failed to setup cookies: {e}")

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    try:
        # Search via YouTube Music API (super clean and stable)
        search_results = ytmusic.search(song_name, filter="songs")
        if not search_results:
            return "Song not found", 404
            
        video_id = search_results[0]["videoId"]
        watch_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "cookiefile": COOKIE_PATH if os.path.exists(COOKIE_PATH) and os.path.getsize(COOKIE_PATH) > 0 else None,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "android_music", "web"]
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(watch_url, download=False)
            if "url" in info:
                return redirect(info["url"], code=302)
                
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Stream URL not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
