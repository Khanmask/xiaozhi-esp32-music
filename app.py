import os
import yt_dlp
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return jsonify({"error": "No song provided"}), 400

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
                    # Return a JSON payload that the firmware can successfully parse!
                    return jsonify({
                        "url": stream_url,
                        "title": entry.get("title", song_name),
                        "artist": entry.get("uploader", "Unknown")
                    })
                    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Song not found on SoundCloud"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
