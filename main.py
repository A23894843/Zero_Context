import os
import sys
import glob
import asyncio
import subprocess
import config
from engine.train_pipeline import train_models
from engine.core import ZeroContextEngine
from engine.database import AsyncThreatDB

def get_kali_keyboard_path()    :
    """Resolves the dynamic keyboard event path native to kali Linux udev rules."""
    for path in glob.glob("/dev/input/by-path/*-kbd"):
        return path

    print ("[!] WARNING: Colud not auto-deect keyboard in /by-path/. Defaulting to event0.")
    return "/dev/input/event0"

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

    active_kbd_path = get_kali_keyboard_path()

    # 2. Launch the C++ daemon in the background (Non-Blocking)
    print("[*] Launching C++ Sensor Daemon with root privileges...")
    print("[*] Note: You may be prompted for your sudo password.")
    sensor_process = subprocess.Popen(["sudo", config.SENSOR_BIN, active_kbd_path])

    # 3. Start the Python UDS Server
    for sock in [config.UDS_MOUSE, config.UDS_KBD] :
        if os.path.exists(sock):
            os.remove(sock)

    db = AsyncThreatDB (host = config.DB_HOST, user = config.DB_USER, password = config.DB_PASS, db = config.DB_NAME)
    await db.connect()
        
    engine = ZeroContextEngine(config, db)
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
        await db.close()

if __name__ == "__main__" :
    try:
        os.remove(os.path.join(config.TEMP_DIR, "zero_context_telemetry.jsonl"))
        print ("Old telemetry ledger cleared.")
        os.makedirs (config.MODEL_DIR, exist_ok = True)
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"Failed to delete telemetry file: {e}")

    try :
        asyncio.run(main())
        train_models()
    except KeyboardInterrupt :
        print("\n[*] ZeroContext System Halted.")

        print ("\n[*] ZeroContext Lifecycle Complete.")