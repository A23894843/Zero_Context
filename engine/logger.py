import json
import time

class Telemetry_Logger :
    def __init__ (self, log_path)   :
        self.log_path = log_path

    def log_event (self, event_type, metadata) :
        """Appends a structured ML feature vector to the JSON Lines log."""
        log_entry = {
            "ingestion_timestamp": time.time(),
            "event_type": event_type,
            "features": metadata
        }
        with open (self.log_path, "a") as log_file :
            log_file.write (json.dumps (log_entry) + "\n")