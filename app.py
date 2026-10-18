import os
import yt_dlp
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return jsonify({"error": "No song provided"}), 400

    # Force yt_dlp to look for direct progressive audio formats instead of HLS playlists
    ydl_opts = {
        "format": "bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "default_search": "scsearch1",
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"scsearch1:{song_name}"
            info = ydl.extract_info(search_query, download=False)
            
            if info and "entries" in info and len(info["entries"]) > 0:
                entry = info["entries"][0]
                if entry:
                    stream_url = entry.get("url")
                    
                    # If formats list is available, extract a direct non-m3u8 audio link
                    if "formats" in entry:
                        for fmt in entry["formats"]:
                            if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none":
                                protocol = fmt.get("protocol", "")
                                if "m3u8" not in protocol and "http" in protocol:
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
    
