import os
import yt_dlp
import asyncio
import websockets
import json
import threading
import subprocess
from flask import Flask, Response, request

# 1. Flask App for HTTP health check and stream transcoding
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
                    # Use ffmpeg to transcode incoming audio into raw PCM stream (16kHz, mono)
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-i", audio_url,
                        "-f", "s16le",
                        "-acodec", "pcm_s16le",
                        "-ar", "16000",
                        "-ac", "1",
                        "pipe:1"
                    ]
                    
                    def generate():
                        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        while True:
                            chunk = process.stdout.read(4096)
                            if not chunk:
                                break
                            yield chunk

                    return Response(generate(), mimetype="application/octet-stream")
                    
    except Exception as e:
        return f"Error: {str(e)}", 500

    return "Song not found", 404

# Run Flask HTTP server on Render port
def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_http_server, daemon=True).start()

# 2. WebSocket MCP Client Loop
XIAOZHI_WSS_URL = os.environ.get("XIAOZHI_WSS_URL", "")
RENDER_MUSIC_URL = os.environ.get("RENDER_MUSIC_URL", "")

async def connect_mcp():
    while True:
        try:
            if not XIAOZHI_WSS_URL:
                await asyncio.sleep(10)
                continue

            async with websockets.connect(XIAOZHI_WSS_URL, ping_interval=20, ping_timeout=20) as ws:
                while True:
                    raw_msg = await ws.recv()
                    data = json.loads(raw_msg)
                    
                    method = data.get("method")
                    req_id = data.get("id")

                    if method == "initialize":
                        await ws.send(json.dumps({
                            "jsonrpc": "2.0",
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {}},
                                "serverInfo": {"name": "music-bridge", "version": "1.0.0"}
                            },
                            "id": req_id
                        }))

                    elif method == "tools/list":
                        await ws.send(json.dumps({
                            "jsonrpc": "2.0",
                            "result": {
                                "tools": [
                                    {
                                        "name": "stream_custom_song",
                                        "description": "Stream custom music directly to the assistant.",
                                        "inputSchema": {
                                            "type": "object",
                                            "properties": {
                                                "song_name": {"type": "string", "description": "Song name"}
                                            },
                                            "required": ["song_name"]
                                        }
                                    }
                                ]
                            },
                            "id": req_id
                        }))

                    elif method == "tools/call":
                        params = data.get("params", {})
                        if params.get("name") == "stream_custom_song":
                            song = params.get("arguments", {}).get("song_name", "")
                            stream_url = f"{RENDER_MUSIC_URL}{song.replace(' ', '%20')}"
                            
                            await ws.send(json.dumps({
                                "jsonrpc": "2.0",
                                "result": {
                                    "content": [
                                        {"type": "text", "text": f"Playing {song} for you!"},
                                        {"type": "resource_link", "uri": stream_url, "name": song, "mimeType": "audio/l16"}
                                    ]
                                },
                                "id": req_id
                            }))

        except Exception as e:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(connect_mcp())
