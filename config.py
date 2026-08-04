import os

# Base Paths
BASE_DIR = os.path.dirname (os.path.abspath (__file__))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
SENSOR_DIR = os.path.join(BASE_DIR, "sensor")

#IPC Socket Paths
UDS_MOUSE = os.path.join(BASE_DIR, "Zero_Context_mouse.sock")
UDS_KBD = os.path.join(BASE_DIR, "Zero_Context_kbd.sock")

# Security Thresholds
VELOCITY_CEILING = 15000   #px/s

# C++ Daemon Paths
SENSOR_BIN = os.path.join(SENSOR_DIR, "sensor_daemon")
SENSOR_SRC = os.path.join(SENSOR_DIR, "sensor_daemon.cpp")

# Persistance  Logging
TELEMETRY_LOG = os.path.join(BASE_DIR, "zero_context_telemetry.jsonl")