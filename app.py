import os
import yt_dlp
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return jsonify({"error": "No song provided"}), 400

    # Switching to YouTube search forces direct progressive audio streams over m3u8 playlists!
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch1"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch1:{song_name}"
            info = ydl.extract_info(search_query, download=False)
            
            if "entries" in info and info["entries"]:
                entry = info["entries"][0]
                
                stream_url = entry.get("url")
                
                # Pick direct audio containers over m3u8 playlists if present
                if "formats" in entry:
                    for fmt in entry["formats"]:
                        if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none":
                            if "m3u8" not in fmt.get("protocol", ""):
                                stream_url = fmt.get("url")
                                break

                if stream_url:
                    return jsonify({
                        "audio_url": stream_url,
                        "title": entry.get("title", song_name),
                        "artist": entry.get("uploader", "Unknown"),
                        "lyric_url": ""
                    })
                    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Song not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
