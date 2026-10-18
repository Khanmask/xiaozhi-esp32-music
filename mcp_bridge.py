import asyncio
import websockets
import json
import os

# Your Xiaozhi WebSocket Endpoint
XIAOZHI_WSS_URL = os.environ.get("XIAOZHI_WSS_URL", "wss://api.xiaozhi.me/mcp/YOUR_TOKEN_HERE")
RENDER_MUSIC_URL = os.environ.get("RENDER_MUSIC_URL", "https://xiaozhi-esp32-music.onrender.com/stream_pcm?song=")

async def connect_mcp():
    while True:
        try:
            print("Connecting to Xiaozhi MCP Server...")
            async with websockets.connect(XIAOZHI_WSS_URL, ping_interval=20, ping_timeout=20) as ws:
                print("Connected to Xiaozhi MCP Server! 🚀")
                
                # 1. Register play_music tool with Lily
                register_msg = {
                    "jsonrpc": "2.0",
                    "method": "tools/register",
                    "params": {
                        "name": "play_music",
                        "description": "Searches and plays a song using direct audio streaming.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "song_name": {"type": "string", "description": "The name of the song requested"}
                            },
                            "required": ["song_name"]
                        }
                    },
                    "id": 1
                }
                await ws.send(json.dumps(register_msg))

                # 2. Listen for voice commands from Lily
                while True:
                    raw_msg = await ws.recv()
                    data = json.loads(raw_msg)
                    
                    if data.get("method") == "tools/call":
                        req_id = data.get("id")
                        params = data.get("params", {})
                        args = params.get("arguments", {})
                        song = args.get("song_name", "")

                        print(f"Lily requested song: {song}")
                        
                        stream_url = f"{RENDER_MUSIC_URL}{song.replace(' ', '%20')}"
                        
                        # Return audio stream link to Lily
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
  
