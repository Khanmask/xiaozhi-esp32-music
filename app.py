import os
import requests
from flask import Flask, redirect, request

app = Flask(__name__)

# Public, reliable Invidious instances that provide direct audio streams freely
INVIDIOUS_INSTANCES = [
    "https://invidious.perennialte.ch",
    "https://vid.priv.au",
    "https://invidious.projectsegfault.net"
]

@app.route("/stream_pcm", methods=["GET"])
def stream_audio():
    song_name = request.args.get("song", "")
    if not song_name:
        return "No song provided", 400

    direct_audio_url = None

    # Try searching via public Invidious instances
    for instance in INVIDIOUS_INSTANCES:
        try:
            search_url = f"{instance}/api/v1/search?q={song_name}&type=video"
            response = requests.get(search_url, timeout=5)
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    video_id = results[0]["videoId"]
                    
                    # Fetch video details to grab the direct adaptive audio stream
                    details_url = f"{instance}/api/v1/videos/{video_id}"
                    details_resp = requests.get(details_url, timeout=5)
                    if details_resp.status_code == 200:
                        data = details_resp.json()
                        adaptive_formats = data.get("adaptiveFormats", [])
                        
                        # Find an audio-only stream
                        for fmt in adaptive_formats:
                            if "audio" in fmt.get("type", "") and "url" in fmt:
                                direct_audio_url = fmt["url"]
                                break
                        
                        if direct_audio_url:
                            break
        except Exception as e:
            print(f"Instance {instance} failed: {e}")
            continue

    if direct_audio_url:
        return redirect(direct_audio_url, code=302)

    return "Song not found or streams blocked", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port)
    
