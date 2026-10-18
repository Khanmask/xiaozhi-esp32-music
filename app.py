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
        "default_search": "scsearch1"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"scsearch1:{song_name}"
            info = ydl.extract_info(search_query, download=False)
            
            if "entries" in info and info["entries"]:
                entry = info["entries"][0]
                stream_url = entry.get("url")
                
                if stream_url:
                    return redirect(stream_url, code=302)
                    
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Song not found on SoundCloud", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
