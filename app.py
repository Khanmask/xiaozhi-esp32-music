import os
import requests
from flask import Flask, redirect, request

app = Flask(__name__)

# Public Piped API instances (alternative YouTube frontends)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.in.projectsegfault.net",
    "https://piped-api.garudalinux.org"
]

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    direct_audio_url = None

    for instance in PIPED_INSTANCES:
        try:
            # Search for the video on Piped
            search_url = f"{instance}/search?q={song_name}&filter=videos"
            response = requests.get(search_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items and len(items) > 0:
                    # Get the watch URL / ID from the first result
                    url_path = items[0].get("url", "")
                    if "v=" in url_path:
                        video_id = url_path.split("v=")[-1]
                    else:
                        continue
                        
                    # Fetch streams for this video
                    streams_url = f"{instance}/streams/{video_id}"
                    streams_resp = requests.get(streams_url, timeout=5)
                    
                    if streams_resp.status_code == 200:
                        stream_data = streams_resp.json()
                        audio_streams = stream_data.get("audioStreams", [])
                        
                        # Find a working audio stream url
                        if audio_streams:
                            # Pick the first available audio stream URL
                            direct_audio_url = audio_streams[0].get("url")
                            if direct_audio_url:
                                break
        except Exception as e:
            print(f"Piped instance {instance} failed: {e}")
            continue

    if direct_audio_url:
        return redirect(direct_audio_url, code=302)

    return "Song not found or streams blocked", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
