import time
import math
from pynput import mouse, keyboard

class Telemetry_sensor :
    def __init__ (self) :
        self.previous_position = None
        self.previous_time = None
        self.key_press_timers = {}

    def on_move (self, x, y)    :
        current_time = time.time()

        if self.previous_position is None :
            self.previous_position = (x, y)
            self.previous_time = current_time
            return

        delta_t = current_time - self.previous_time

        if delta_t == 0 :
            delta_t = 0.0001

        dx = x - self.previous_position[0]
        dy = y - self.previous_position[1]
        displacement = math.sqrt(dx**2 + dy**2)

        if displacement > 0 :
            velocity = displacement / delta_t

            print (f"Mouse moved to {x}, {y} with velocity: {velocity :> 0.2f} pixels/sec")

            if velocity > 15000:
                print("\n[!] SECURITY ALERT: Kinematic anomaly detected.")
                print(f"[!] Velocity recorded at {velocity:.2f} px/s.")
                print("[!] Suspected device handover, KVM switch, or automated session injection.")
                print("[!] Halting execution pipeline.")

        self.previous_position = (x, y)
        self.previous_time = current_time

    def on_press (self, key) :
        try :
            char = key.char
        except AttributeError :
            char = str(key)

        if char not in self.key_press_timers :
            self.key_press_timers[char] = time.time()

    def on_release (self, key) :
        try :
            char = key.char
        except AttributeError :
            char = str(key)

        if char in self.key_press_timers :
            dwell_time = time.time() - self.key_press_timers[char]
            print (f"Key '{char}' released after {dwell_time:.2f} seconds.")
            del self.key_press_timers[char]

        if key == keyboard.Key.esc :
            print("\n [*] Escape key detected. Shutting down telemetry stream.")
            return False

    def initialize_stream (self) :
        print ("[+] ZeroContext Event-Driven Telemetry Sensor v1.0")
        print ("[+] Initializing telemetry stream...")
        mouse_listener = mouse.Listener (on_move = self.on_move)
        keyboard_listener = keyboard.Listener (on_press = self.on_press, on_release = self.on_release)

        mouse_listener.start()
        keyboard_listener.start()

        mouse_listener.join()
        keyboard_listener.join()

        mouse_listener.stop()
        keyboard_listener.stop()

if __name__ == "__main__" :
    sensor = Telemetry_sensor()
    sensor.initialize_stream()