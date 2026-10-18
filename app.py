import os
import requests
from flask import Flask, redirect, request

app = Flask(__name__)

# Active public Piped API mirrors
PIPED_APIS = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.yt",
    "https://pipedapi.privacy.com.de"
]

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    direct_audio_url = None

    for api in PIPED_APIS:
        try:
            # 1. Search for the song
            search_res = requests.get(f"{api}/search?q={song_name}&filter=videos", timeout=4)
            if search_res.status_code == 200:
                items = search_res.json().get("items", [])
                if items:
                    url_path = items[0].get("url", "")
                    if "v=" in url_path:
                        video_id = url_path.split("v=")[-1]
                        
                        # 2. Fetch stream details using the video ID
                        stream_res = requests.get(f"{api}/streams/{video_id}", timeout=4)
                        if stream_res.status_code == 200:
                            audio_streams = stream_res.json().get("audioStreams", [])
                            if audio_streams:
                                # Pick the first available audio stream URL
                                direct_audio_url = audio_streams[0].get("url")
                                if direct_audio_url:
                                    break
        except Exception as e:
            print(f"Mirror {api} failed: {e}")
            continue

    if direct_audio_url:
        return redirect(direct_audio_url, code=302)

    return "Stream lookup failed, please try again", 504

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
