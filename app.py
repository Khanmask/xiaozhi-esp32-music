import os
import base64
import re
import yt_dlp
from flask import Flask, redirect, request

app = Flask(__name__)

COOKIE_PATH = "/tmp/cookies.txt"
cookies_base64 = os.environ.get("YT_COOKIES_BASE64")

if cookies_base64:
    try:
        # Strip all whitespace, tabs, newlines, and accidental quotes
        cookies_base64 = "".join(cookies_base64.split()).strip('"\'')
        
        # Keep ONLY valid Base64 characters to completely eliminate padding/character errors
        cookies_base64 = re.sub(r'[^A-Za-z0-9+/=]', '', cookies_base64)
        
        # Automatically fix missing padding characters (=)
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

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "cookiefile": COOKIE_PATH if os.path.exists(COOKIE_PATH) and os.path.getsize(COOKIE_PATH) > 0 else None,
        # Use web client first to handle text searches properly, falling back to ios/mweb
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "mweb", "ios"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch1:{song_name}"
            info = ydl.extract_info(search_query, download=False)
            
            if "entries" in info:
                entries = info["entries"]
                if entries and len(entries) > 0:
                    direct_audio_url = entries[0]["url"]
                    return redirect(direct_audio_url, code=302)
            elif "url" in info:
                return redirect(info["url"], code=302)
                
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Song not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
