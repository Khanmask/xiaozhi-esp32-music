import os
import re
import yt_dlp
from flask import Flask, jsonify, request

app = Flask(__name__)

def fetch_audio_info(search_query):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        if info and "entries" in info and len(info["entries"]) > 0:
            entry = info["entries"][0]
            if entry:
                stream_url = entry.get("url")
                
                # Filter out m3u8 playlists if a direct HTTP stream format exists
                if "formats" in entry:
                    for fmt in entry["formats"]:
                        if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none":
                            protocol = fmt.get("protocol", "")
                            if "m3u8" not in protocol and "http" in protocol:
                                stream_url = fmt.get("url")
                                break
                                
                if stream_url:
                    return {
                        "audio_url": stream_url,
                        "title": entry.get("title", search_query),
                        "artist": entry.get("uploader", "Unknown"),
                        "lyric_url": ""
                    }
    return None

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    # Clean up weird speech-to-text spacing (e.g., "J+H+O+N" -> "J H O N")
    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()

    try:
        # 1. Try YouTube search first for direct progressive streams
        result = fetch_audio_info(f"ytsearch1:{clean_song}")
        
        # 2. If YouTube fails, fallback to SoundCloud search
        if not result:
            result = fetch_audio_info(f"scsearch1:{clean_song}")

        if result:
            return jsonify(result)

    except Exception as e:
        print(f"Render Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Song not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
