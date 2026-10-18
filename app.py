import os
import yt_dlp
from flask import Flask, redirect, request

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        # The embedded web player client bypasses standard datacenter blocks
        "extractor_args": {
            "youtube": {
                "player_client": ["web_embedded"]
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
            
            if "entries" in info and info["entries"]:
                entry = info["entries"][0]
                stream_url = entry.get("url")
                
                # If direct URL wasn't in the search wrapper, resolve via watch ID
                if not stream_url and "id" in entry:
                    video_id = entry["id"]
                    direct_info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    stream_url = direct_info.get("url")
                
                if stream_url:
                    return redirect(stream_url, code=302)
                    
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Song lookup failed", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
