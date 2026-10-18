import os
import yt_dlp
import requests
from flask import Flask, Response, request

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
                audio_url = entry.get("url")
                
                if audio_url:
                    def generate():
                        external_stream = requests.get(audio_url, stream=True)
                        for chunk in external_stream.iter_content(chunk_size=4096):
                            if chunk:
                                yield chunk

                    return Response(generate(), mimetype="audio/mpeg")
                    
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Song not found on SoundCloud", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
