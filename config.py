import os

# Base Paths
BASE_DIR = os.path.dirname (os.path.abspath (__file__))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
SENSOR_DIR = os.path.join(BASE_DIR, "sensor")

# Security Thresholds
VELOCITY_CEILING = 15000   #px/s

TEMP_DIR = os.path.join(BASE_DIR, "temporary")
MODEL_DIR = os.path.join (BASE_DIR, "models")

UDS_MOUSE = os.path.join(TEMP_DIR, "Zero_Context_mouse.sock")
UDS_KBD = os.path.join(TEMP_DIR, "Zero_Context_kbd.sock")

# C++ Daemon Paths
SENSOR_BIN = os.path.join(SENSOR_DIR, "sensor_daemon")
SENSOR_SRC = os.path.join(SENSOR_DIR, "sensor_daemon.cpp")

# Persistance  Logging
TELEMETRY_LOG = os.path.join(TEMP_DIR, "zero_context_telemetry.jsonl")

# Database Configuration
DB_HOST = "0.0.0.0"
DB_USER = "root"
DB_PASS = "hp122023" # Update this if your root user has a password
DB_NAME = "ZeroContext"