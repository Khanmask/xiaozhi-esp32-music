import os
import requests
from flask import Flask, redirect, request

app = Flask(__name__)

# Verified public Piped API mirrors
PIPED_APIS = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.in.projectsegfault.net"
]

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    for api in PIPED_APIS:
        try:
            # Search query
            search_res = requests.get(f"{api}/search?q={song_name}&filter=videos", timeout=4)
            if search_res.status_code == 200:
                items = search_res.json().get("items", [])
                if items:
                    url_path = items[0].get("url", "")
                    if "v=" in url_path:
                        video_id = url_path.split("v=")[-1]
                        
                        # Get stream details
                        stream_res = requests.get(f"{api}/streams/{video_id}", timeout=4)
                        if stream_res.status_code == 200:
                            audio_streams = stream_res.json().get("audioStreams", [])
                            if audio_streams:
                                stream_url = audio_streams[0].get("url")
                                if stream_url:
                                    return redirect(stream_url, code=302)
        except Exception as e:
            print(f"API {api} error: {e}")
            continue

    return "Stream lookup failed", 504

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    import os
import requests
from flask import Flask, redirect, request

app = Flask(__name__)

# Verified public Piped API mirrors
PIPED_APIS = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.in.projectsegfault.net"
]

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    for api in PIPED_APIS:
        try:
            # Search query
            search_res = requests.get(f"{api}/search?q={song_name}&filter=videos", timeout=4)
            if search_res.status_code == 200:
                items = search_res.json().get("items", [])
                if items:
                    url_path = items[0].get("url", "")
                    if "v=" in url_path:
                        video_id = url_path.split("v=")[-1]
                        
                        # Get stream details
                        stream_res = requests.get(f"{api}/streams/{video_id}", timeout=4)
                        if stream_res.status_code == 200:
                            audio_streams = stream_res.json().get("audioStreams", [])
                            if audio_streams:
                                stream_url = audio_streams[0].get("url")
                                if stream_url:
                                    return redirect(stream_url, code=302)
        except Exception as e:
            print(f"API {api} error: {e}")
            continue

    return "Stream lookup failed", 504

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
