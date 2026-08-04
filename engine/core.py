import json
import math
import asyncio
from engine.logger import Telemetry_Logger

class ZeroContextEngine :
    def __init__ (self, config) :
        self.prev_x, self.prev_y, self.prev_t = 0, 0, 0.0
        self.key_press_timers = {}

        self.config = config
        self.logger = Telemetry_Logger (config.TELEMETRY_LOG)

        self.prev_velocity = 0.0
        self.prev_key_release_time = 0.0

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
                    acceleration = (velocity - self.prev_velocity) / delta_t
                    angle = math.degrees (math.atan2 (dx, dy))
                    
                    self.logger.log_event("MOUSE_FEATURES", {
                                            "delta_t": round(delta_t, 6),
                                            "velocity": round(velocity, 2),
                                            "acceleration": round(acceleration, 2),
                                            "angle_degrees": round(angle, 2)
                                        })
                    
                    if velocity > self.config.VELOCITY_CEILING:
                        print ("\r[!] SECURITY ALERT: Kinematic anomaly detected (Non-human velocity).")

                    self.prev_velocity = velocity
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

                if state == 1 :
                    self.key_press_timers[key_code] = timestamp
                    # Add _time to the variable name
                    flight_time = timestamp - self.prev_key_release_time if self.prev_key_release_time > 0 else 0.0
                    self.key_press_timers [f"flight_{key_code}"] = flight_time

                elif state == 0 and key_code in self.key_press_timers :
                    dwell_time = timestamp - self.key_press_timers [key_code]
                    flight_time = self.key_press_timers.get (f"flight_{key_code}", 0.0)

                    self.logger.log_event("KEYBOARD_FEATURES", {
                                            "key_code": key_code,
                                            "dwell_time": round(dwell_time, 4),
                                            "flight_time": round(flight_time, 4)
                                        })

                    self.prev_key_release_time = timestamp
                    del self.key_press_timers[key_code]
                    if f"flight_{key_code}" in self.key_press_timers :
                        del self.key_press_timers[f"flight_{key_code}"]

        except asyncio.CancelledError :
            pass

        finally :
            writer.close()