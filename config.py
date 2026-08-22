import os
from dotenv import load_dotenv

load_dotenv()

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

# Database Configuration (loaded from .env — never commit real credentials)
DB_HOST = os.getenv("ZC_DB_HOST", "127.0.0.1")
DB_USER = os.getenv("ZC_DB_USER", "root")
DB_PASS = os.getenv("ZC_DB_PASS", "")
DB_NAME = os.getenv("ZC_DB_NAME", "ZeroContext")

# Dashboard
DASHBOARD_PORT = int(os.getenv("ZC_DASHBOARD_PORT", "8000"))
