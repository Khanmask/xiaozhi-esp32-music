import os
import yt_dlp
from ytmusicapi import YTMusic
from flask import Flask, redirect, request

app = Flask(__name__)
ytmusic = YTMusic()

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

        # Using Android clients completely bypasses web signature blocks!
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
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
    
