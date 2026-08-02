import os
import sys
import json
import math
import time
import asyncio
import socket
import subprocess

BASE_DIR = os.getcwd()
UDS_MOUSE = BASE_DIR + "/Zero_Context_mouse.sock"
UDS_KBD = BASE_DIR + "/Zero_Context_kbd.sock"
VELOCITY_CEILING = 15000   #px/s

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENSOR_BIN = os.path.join(BASE_DIR, "sensor_daemon")
SENSOR_SRC = os.path.join(BASE_DIR, "sensor_daemon.cpp")

class ZeroContextEngine :
    def __init__ (self) :
        self.prev_x, self.prev_y, self.prev_t = 0, 0, 0.0
        self.key_press_timers = {}

    async def handle_mouse(self, reader, writer):
        # Force Carriage Return (\r) on all print statements to fix terminal alignment
        print("[*] Mouse IPC Channel Established")
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

    async def handle_keyboard (self, reader, writer) :
        print("[*] Keyboard IPC Channel Established.")
        try :
            while True :
                data = await reader.readline()
                if not data :
                    break

                try :
                    payload = json.loads(data.decode().strip())
                except json.JSONDecodeError :
                        continue

                key_code = payload['key_code']
                state = payload['state']
                timestamp = payload['timestamp']

                print(f"\r[*] RAW KBD STREAM - KeyCode: {key_code} | State: {state}")

                if state == 1 :
                    self.key_press_timers[key_code] = timestamp

                elif state == 0 and key_code in self.key_press_timers :
                    dwell_time = timestamp - self.key_press_timers [key_code]
                    print (f"\r[Keyboard] KeyCode: {key_code :> 3} | Dwell Time: {dwell_time :.4f} seconds")

                    del self.key_press_timers[key_code]

                    if dwell_time < 0.01 :
                        print ("\r[!] SECURITY ALERT: Non-human Dwell Time detected. Possible Script injection.")

        except asyncio.CancelledError :
                    pass

async def main():
    # 1. Auto-Compile the C++ daemon if needed (Blocking is fine here)
    if not os.path.exists(SENSOR_BIN):
        print("[*] Compiling Multi-Threaded C++ Daemon...")
        try:
            subprocess.run(["g++", "-pthread", SENSOR_SRC, "-o", SENSOR_BIN], check=True)
            print("[*] Compilation successful.")
        except subprocess.CalledProcessError:
            print("[!] FATAL: Compilation failed.")
            exit(1)

    # 2. Launch the C++ daemon in the background (Non-Blocking)
    print("[*] Launching C++ Sensor Daemon with root privileges...")
    print("[*] Note: You may be prompted for your sudo password.")
    sensor_process = subprocess.Popen(["sudo", SENSOR_BIN])

    # 3. Start the Python UDS Server
    for sock in [UDS_MOUSE, UDS_KBD] :
            if os.path.exists(sock):
                os.remove(sock)
        
    engine = ZeroContextEngine()
    mouse_server = await asyncio.start_unix_server(engine.handle_mouse, path = UDS_MOUSE)
    kbd_server = await asyncio.start_unix_server(engine.handle_keyboard, path = UDS_KBD)
    
    print(f"[*] ZeroContext Backend listening on {UDS_MOUSE}")
    
    try:
        async with mouse_server, kbd_server:
            await asyncio.gather(mouse_server.serve_forever(), kbd_server.serve_forever())
    finally:
        # 4. Clean up the C++ process if the Python server shuts down
        print("\n[*] Shutting down C++ Sensor Daemon...")
        sensor_process.terminate()

if __name__ == "__main__" :
    try :
        asyncio.run(main())
    except KeyboardInterrupt :
        print("\n[*] ZeroContext System Halted.")