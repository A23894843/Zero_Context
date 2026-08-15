import os
import json
import math
import asyncio
import joblib
import numpy as np
import torch
import torch.nn as nn
from engine.logger import Telemetry_Logger
from engine.train_pipeline import *

class ZeroContextEngine :
    def __init__ (self, config, db) :
        self.prev_x, self.prev_y, self.prev_t = 0, 0, 0.0
        self.key_press_timers = {}

        self.config = config
        self.logger = Telemetry_Logger (config.TELEMETRY_LOG)

        self.prev_velocity = 0.0
        self.prev_key_release_time = 0.0

        self.AUTOENCODER_THRESHOLD  = 0.35
        self.last_mouse_alert = 0.0

        ae_path = os.path.join(config.MODEL_DIR, "mouse_autoencoder.pth")
        self.mouse_model = MouseAutoEncoder()

        self.db = db

        if os.path.exists (ae_path) :
            self.mouse_model.load_state_dict (torch.load (ae_path, weights_only = True))
            self.mouse_model.eval()
            print ("[+] Deep Learning Mouse Autoencoder loaded.")
        else :
            self.mouse_model = None

        kbd_path = os.path.join (config.MODEL_DIR, "kbd_iforest.pkl")
        if os.path.exists (kbd_path)    :
            self.kbd_model = joblib.load (kbd_path)
            print ("[+] Keystroke Isolation Forest loaded.")
        else :
            self.kbd_model = None

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

                    if self.mouse_model is not None :
                        norm_v = min (max (velocity / 15000.0, 0.0), 1.0)
                        norm_a = min (max (abs (acceleration) / 50000.0, 0.0), 1.0)
                        norm_dt = min (max (delta_t / 0.1, 0.0), 1.0)

                        input_tensor = torch.tensor ([[norm_v, norm_a, norm_dt]], dtype = torch.float32)

                        with torch.no_grad()    :
                            reconstruction = self.mouse_model (input_tensor)
                            mse_loss = torch.mean ((input_tensor - reconstruction) ** 2).item()

                        if current_t - self.last_mouse_alert > 1.0 :
                            if mse_loss > self.AUTOENCODER_THRESHOLD  :
                                print(f"\r[🚨 MOUSE ANOMALY] High Reconstruction Loss: {mse_loss:.4f} | Non-Human Pattern")
                                await self.db.log_threat ("MOUSE_KINEMATICS", float (mse_loss), "High Reconstruction Loss: Non-Human Pattern")
                                self.last_mouse_alert = current_t
                 
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

                    if self.kbd_model is not None :
                        norm_dwell = min (max (dwell_time / 2.0, 0.0), 1.0)
                        norm_flight = min (max (flight_time / 2.0, 0.0), 1.0)

                        tensor_x = np.array ([[norm_dwell, norm_flight]])
                        prediction = self.kbd_model.predict (tensor_x)[0]

                        if prediction == -1 :
                            print("\r[🚨 KEYBOARD ANOMALY] Suspicious keystroke rhythm detected.")
                            await self.db.log_threat ("KEYBOARD_DYNAMICS", float (prediction), "Suspicious keystroke rhythm detected.")

                    self.prev_key_release_time = timestamp
                    del self.key_press_timers[key_code]
                    if f"flight_{key_code}" in self.key_press_timers :
                        del self.key_press_timers[f"flight_{key_code}"]

        except asyncio.CancelledError :
            pass

        finally :
            writer.close()