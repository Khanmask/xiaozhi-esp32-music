import os
import re
import yt_dlp
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    raw_song = request.args.get("song", "")
    if not raw_song:
        return jsonify({"error": "No song provided"}), 400

    clean_song = re.sub(r'[\s+]+', ' ', raw_song).strip()

    # Configure yt_dlp to look specifically for direct progressive audio formats
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "default_search": "ytsearch1", # Prioritize YouTube for direct streams
        "nocheckcertificate": True,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{clean_song}", download=False)
            
            stream_url = None
            title = clean_song
            artist = "Unknown"

            if info and "entries" in info and len(info["entries"]) > 0:
                entry = info["entries"][0]
                if entry:
                    title = entry.get("title", clean_song)
                    artist = entry.get("uploader", "Unknown")
                    
                    # Search through available formats for a direct link (non-m3u8)
                    if "formats" in entry:
                        for fmt in entry["formats"]:
                            if fmt.get("vcodec") == "none" and fmt.get("acodec") != "none":
                                protocol = fmt.get("protocol", "")
                                if "m3u8" not in protocol:
                                    stream_url = fmt.get("url")
                                    break
                    
                    # Fallback to default entry URL if no direct format matched
                    if not stream_url:
                        stream_url = entry.get("url")

            if stream_url and "m3u8" not in stream_url:
                return jsonify({
                    "audio_url": stream_url,
                    "title": title,
                    "artist": artist,
                    "lyric_url": ""
                })

    except Exception as e:
        print(f"Render Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Song not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
