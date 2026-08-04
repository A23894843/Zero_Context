import os
import sys
import json
import math
import time
import asyncio
import socket
import subprocess
import config
from engine.core import ZeroContextEngine

async def main():
    # 1. Auto-Compile the C++ daemon if needed (Blocking is fine here)
    if not os.path.exists(config.SENSOR_BIN):
        print("[*] Compiling Multi-Threaded C++ Daemon...")
        try:
            subprocess.run(["g++", "-pthread", config.SENSOR_SRC, "-o", config.SENSOR_BIN], check=True)
            print("[*] Compilation successful.")
        except subprocess.CalledProcessError:
            print("[!] FATAL: Compilation failed.")
            exit(1)

    # 2. Launch the C++ daemon in the background (Non-Blocking)
    print("[*] Launching C++ Sensor Daemon with root privileges...")
    print("[*] Note: You may be prompted for your sudo password.")
    sensor_process = subprocess.Popen(["sudo", config.SENSOR_BIN])

    # 3. Start the Python UDS Server
    for sock in [config.UDS_MOUSE, config.UDS_KBD] :
            if os.path.exists(sock):
                os.remove(sock)
        
    engine = ZeroContextEngine(config)
    mouse_server = await asyncio.start_unix_server(engine.handle_mouse, path = config.UDS_MOUSE)
    kbd_server = await asyncio.start_unix_server(engine.handle_keyboard, path = config.UDS_KBD)
    
    print(f"[*] ZeroContext Backend listening on {config.UDS_MOUSE}")
    
    try:
        async with mouse_server, kbd_server:
            await asyncio.gather(mouse_server.serve_forever(), kbd_server.serve_forever())
    finally:
        # 4. Clean up the C++ process if the Python server shuts down
        print("\n[*] Shutting down C++ Sensor Daemon...")
        sensor_process.terminate()

if __name__ == "__main__" :
    try:
        os.remove(os.path.join(config.BASE_DIR, "zero_context_telemetry.jsonl"))
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"Failed to delete telemetry file: {e}")

    try :
        asyncio.run(main())
    except KeyboardInterrupt :
        print("\n[*] ZeroContext System Halted.")