import os
import json
import joblib
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import IsolationForest
import config

class MouseAutoEncoder (nn.Module)  :
    def __init__ (self, input_dim = 3)  :
        super (MouseAutoEncoder, self).__init__()
        self.encoder = nn.Sequential (
            nn.Linear (input_dim, 16), nn.ReLU(),
            nn.Linear (16, 8), nn.ReLU(),
            nn.Linear (8, 4)
        )
        self.decoder = nn.Sequential (
            nn.Linear (4, 8), nn.ReLU(),
            nn.Linear (8, 16), nn.ReLU(),
            nn.Linear (16, input_dim), nn.Sigmoid()
        )

    def forward (self, x) :
        return self.decoder (self.encoder(x))

def load_datasets (log_file) :
    mouse_data, kbd_data = [], []

    if not os.path.exists (log_file) :
        print (f"[!] Log file {log_file} msiing. Run main.py to generate telemetry.")
        return None, None

    print (f"[*] Parsing telemetry ledger: {log_file}")
    with open (log_file, "r") as f :
        for line in f :
            try :
                entry = json.loads (line.strip())
                feat = entry ["features"]

                if entry.get ("event_type") == "MOUSE_FEATURES" :
                    norm_v = min (max (feat["velocity"] / 15000.0, 0.0), 1.0)
                    norm_a = min (max (abs (feat["acceleration"]) / 50000.0, 0.0), 1.0)
                    norm_dt = min (max (feat["delta_t"] / 0.1, 0.0), 1.0)
                    mouse_data.append ([norm_v, norm_a, norm_dt])

                elif entry.get ("event_type") == "KEYBOARD_FEATURES" :
                    norm_dwell = min (max (feat["dwell_time"] / 2.0, 0.0), 1.0)
                    norm_flight = min (max (feat["flight_time"] / 2.0, 0.0), 1.0)
                    kbd_data.append ([norm_dwell, norm_flight])

            except (json.JSONDecodeError, KeyError) :
                continue

    return np.array (mouse_data, dtype = np.float32), np.array (kbd_data, dtype = np.float32)

def train_models() :
    mouse_train, kbd_train = load_datasets (config.TELEMETRY_LOG)

    if mouse_train is not None and len (mouse_train) > 50 :
        print (f"\n[*] Training PyTorch Autoencoder on {len(mouse_train)} mouse frames...")
        model_ae = MouseAutoEncoder()
        criterion = nn.MSELoss()
        optimizer = optim.Adam (model_ae.parameters(), lr = 0.01)

        tensor_x = torch.tensor (mouse_train)

        model_ae.train()

        for epoch in range(50):
            optimizer.zero_grad()
            outputs = model_ae(tensor_x)
            loss = criterion(outputs, tensor_x)
            loss.backward()
            optimizer.step()

        torch.save(
            model_ae.state_dict(),
            os.path.join(config.MODEL_DIR, "mouse_autoencoder.pth")
        )

        print(f"[+] Mouse Autoencoder trained. Final Loss: {loss.item():.6f}")

    else :
        print ("\n[!] Not Enough mouse data to train Autoencoder. Collect more telemtry.")

    if kbd_train is not None and len (kbd_train) > 20 :
        print (f"\n[*] Training Scikit-Learn Isolation Forest on {len (kbd_train)} keystrokes...")
        model_if = IsolationForest (n_estimators = 100, contamination = 0.05, random_state = 42)
        model_if.fit (kbd_train)

        joblib.dump (model_if, os.path.join (config.MODEL_DIR, "kbd_iforest.pkl"))
        print ("[+] Keyboard Isolation Forest successfully trained.")

    else :
        print ("\n[!] Not enough keyboard data to train Isolation Forest . Type more and re-run.")

if __name__ == "__main__"   :
    train_models()