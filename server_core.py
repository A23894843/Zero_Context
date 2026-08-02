import os
import sys
import json
import math
import time
import asyncio
import socket
import subprocess

BASE_DIR = os.getcwd()
UDS_PATH = BASE_DIR + "/Zero_Context_mouse.sock"
VELOCITY_CEILING = 5000   #px/s

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENSOR_BIN = os.path.join(BASE_DIR, "sensor_daemon")
SENSOR_SRC = os.path.join(BASE_DIR, "sensor_daemon.cpp")

class ZeroContextEngine :
    def __init__ (self) :
        self.prev_x, self.prev_y, self.prev_t = 0, 0, 0.0

    async def handle_client(self, reader, writer):
        # Force Carriage Return (\r) on all print statements to fix terminal alignment
        print("[*] C++ Sensor Daemon Connected via UDS.\r")
        try:
            while True:
                # Use readline() to guarantee we process exactly one complete JSON packet at a time
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    payload = json.loads(data.decode().strip())
                except json.JSONDecodeError:
                    # Silently skip malformed packets if a stream collision occurs
                    continue
                    
                dx, dy, current_t = payload['dx'], payload['dy'], payload['timestamp']
                
                # Math: Calculate time-delta and instantaneous velocity
                delta_t = current_t - self.prev_t
                if delta_t == 0: delta_t = 0.0001
                
                displacement = math.sqrt(dx**2 + dy**2)
                
                if displacement > 0 and self.prev_t != 0:
                    velocity = displacement / delta_t
                    
                    # \r forces the cursor back to the start of the terminal line
                    print (f"\rDisplacement: {displacement:>5.2f} px | Velocity: {velocity:>7.2f} px/s")
                    
                    if velocity > VELOCITY_CEILING:
                        print ("\r[!] SECURITY ALERT: Kinematic anomaly detected (Non-human velocity).")
                        
                self.prev_t = current_t
                
        except asyncio.CancelledError:
            pass
        finally:
            print("\n[*] Sensor Disconnected.")
            writer.close()

async def main():
    # 1. Auto-Compile the C++ daemon if needed (Blocking is fine here)
    if not os.path.exists(SENSOR_BIN):
        print("[*] C++ Sensor Daemon binary not found. Compiling now...")
        try:
            subprocess.run(["g++", SENSOR_SRC, "-o", SENSOR_BIN], check=True)
            print("[*] Compilation successful.")
        except subprocess.CalledProcessError:
            print("[!] FATAL: Compilation failed.")
            exit(1)

    # 2. Launch the C++ daemon in the background (Non-Blocking)
    print("[*] Launching C++ Sensor Daemon with root privileges...")
    print("[*] Note: You may be prompted for your sudo password.")
    sensor_process = subprocess.Popen(["sudo", SENSOR_BIN])

    # 3. Start the Python UDS Server
    if os.path.exists(UDS_PATH):
        os.remove(UDS_PATH)
        
    engine = ZeroContextEngine()
    server = await asyncio.start_unix_server(engine.handle_client, path = UDS_PATH)
    
    print(f"[*] ZeroContext Backend listening on {UDS_PATH}")
    
    try:
        async with server:
            await server.serve_forever()
    finally:
        # 4. Clean up the C++ process if the Python server shuts down
        print("\n[*] Shutting down C++ Sensor Daemon...")
        sensor_process.terminate()

if __name__ == "__main__" :
    try :
        asyncio.run(main())
    except KeyboardInterrupt :
        print("\n[*] ZeroContext System Halted.")