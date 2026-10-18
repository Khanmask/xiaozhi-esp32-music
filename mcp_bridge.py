import asyncio
import websockets
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Dummy HTTP server to satisfy Render's Free Web Service port requirement
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Xiaozhi MCP Bridge is running!")

    def log_message(self, format, *args):
        return

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

XIAOZHI_WSS_URL = os.environ.get("XIAOZHI_WSS_URL", "")
RENDER_MUSIC_URL = os.environ.get("RENDER_MUSIC_URL", "https://xiaozhi-esp32-music.onrender.com/stream_pcm?song=")

async def connect_mcp():
    while True:
        try:
            print("Connecting to Xiaozhi MCP Server...")
            async with websockets.connect(XIAOZHI_WSS_URL, ping_interval=20, ping_timeout=20) as ws:
                print("Connected to Xiaozhi MCP Server! 🚀")
                
                while True:
                    raw_msg = await ws.recv()
                    data = json.loads(raw_msg)
                    print(f"Received message: {data}")
                    
                    method = data.get("method")
                    req_id = data.get("id")

                    # Handle tool discovery / listing request from Xiaozhi
                    if method == "tools/list":
                        response_msg = {
                            "jsonrpc": "2.0",
                            "result": {
                                "tools": [
                                    {
                                        "name": "play_music",
                                        "description": "Searches and plays a song using direct audio streaming.",
                                        "inputSchema": {
                                            "type": "object",
                                            "properties": {
                                                "song_name": {"type": "string", "description": "The name of the song requested"}
                                            },
                                            "required": ["song_name"]
                                        }
                                    }
                                ]
                            },
                            "id": req_id
                        }
                        await ws.send(json.dumps(response_msg))
                        print("Sent tools/list response! 🎶")

                    # Handle actual tool execution when Lily calls it
                    elif method == "tools/call":
                        params = data.get("params", {})
                        args = params.get("arguments", {})
                        song = args.get("song_name", "")

                        print(f"Lily requested song: {song}")
                        stream_url = f"{RENDER_MUSIC_URL}{song.replace(' ', '%20')}"
                        
                        response_msg = {
                            "jsonrpc": "2.0",
                            "result": {
                                "content": [
                                    {"type": "text", "text": f"Playing: {stream_url}"}
                                ]
                            },
                            "id": req_id
                        }
                        await ws.send(json.dumps(response_msg))

        except Exception as e:
            print(f"Connection lost ({e}). Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(connect_mcp())
    
