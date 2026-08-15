# Zero_Context

## Overview

**Zero_Context** is an advanced, hybrid **Intrusion Detection and Prevention System (IDPS)** designed to monitor system logs and live network traffic, detect anomalous behavior, and support real-time defensive actions.

The **Cyber Defensive Engine v1.0** combines:

* High-performance **C++ network packet capture**
* **Python-based security intelligence**
* Unsupervised **machine learning**
* Real-time system log monitoring
* Persistent **MySQL threat logging**
* Inter-process communication between the C++ sensor and Python engine
* A web-based **real-time security dashboard**

The architecture is designed to detect suspicious activities such as **DDoS behavior, port scanning, abnormal network traffic, and malicious log activity**.

---

## System Architecture

The system is divided into two primary operational layers:

### 1. Sensor Node — C++

The C++ sensor operates close to the network layer and captures live packets using **libpcap**.

Responsibilities include:

* Capturing network packets
* Extracting network telemetry
* Processing traffic with minimal latency
* Forwarding telemetry to the Python intelligence engine
* Running with the privileges required for raw packet capture

### 2. Intelligence Engine — Python

The Python engine acts as the central security intelligence layer.

Responsibilities include:

* Receiving telemetry from the C++ sensor
* Monitoring system logs
* Extracting security-related features
* Running machine learning models
* Detecting anomalous behavior
* Recording security events
* Coordinating defensive responses
* Providing data to the monitoring dashboard

---

## Architecture Flow

```text
                  ┌──────────────────────────┐
                  │      Network Traffic     │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │     C++ Sensor Node      │
                  │       libpcap            │
                  │                          │
                  │  Packet Capture          │
                  │  Traffic Extraction      │
                  └────────────┬─────────────┘
                               │
                               │ IPC / Telemetry
                               ▼
                  ┌──────────────────────────┐
                  │    Python Intelligence   │
                  │         Engine           │
                  │                          │
                  │  Log Monitoring          │
                  │  Feature Extraction      │
                  │  ML Detection            │
                  │  Threat Analysis         │
                  └────────────┬─────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
       ┌──────────────────┐       ┌──────────────────┐
       │      MySQL       │       │  Web Dashboard   │
       │ Threat Storage   │       │ Real-Time View   │
       └──────────────────┘       └──────────────────┘
```

---

## Repository Structure

```text
Zero_Context/
│
├── main.py                     # Main entry point for the intelligence engine
├── config.py                   # Global configuration and environment settings
├── dashboard.py                # Web dashboard backend
│
├── engine/
│   ├── __init__.py
│   ├── core.py                 # Core detection and IPC logic
│   ├── database.py             # MySQL integration and threat persistence
│   ├── logger.py               # Application and security event logging
│   └── train_pipeline.py       # ML training and model evaluation pipeline
│
├── sensor/
│   ├── sensor.cpp              # Low-level packet capture and telemetry
│   └── sensor_daemon.cpp       # Persistent sensor daemon
│
└── templates/
    └── index.html              # Web dashboard frontend
```

---

## Key Features

### 🔹 Hybrid C++ + Python Architecture

Combines the performance of C++ packet processing with the flexibility of Python for machine learning, analytics, and orchestration.

### 🔹 Machine Learning Threat Detection

Uses unsupervised machine learning techniques to establish behavioral baselines and identify deviations that may represent previously unseen threats.

Potential detection targets include:

* Network anomalies
* Abnormal traffic patterns
* Port scanning
* DDoS-like behavior
* Unusual system activity

### 🔹 Real-Time Network Monitoring

The C++ sensor captures live network traffic and forwards telemetry to the intelligence engine for analysis.

### 🔹 System Log Monitoring

The engine can monitor security-relevant system logs and identify suspicious patterns such as:

```text
Failed password
Invalid user
Authentication failure
Suspicious login activity
```

### 🔹 Persistent Threat Logging

Security events and threat metadata are stored in **MySQL**, allowing historical analysis and investigation.

### 🔹 Interactive Security Dashboard

The web dashboard provides administrators with a centralized view of:

* Network activity
* Detected anomalies
* Security events
* Threat information
* System monitoring data
* Engine status

---

## Technology Stack

| Component             | Technology                                         |
| --------------------- | -------------------------------------------------- |
| Programming Languages | C++, Python                                        |
| Network Capture       | libpcap                                            |
| Machine Learning      | Scikit-learn / Python ML stack                     |
| Backend               | Python                                             |
| Web Dashboard         | Flask                                              |
| Database              | MySQL                                              |
| Operating System      | Kali Linux / Debian-based Linux                    |
| IPC                   | Inter-process communication between C++ and Python |
| Frontend              | HTML / CSS / JavaScript                            |

---

## Machine Learning Pipeline

The ML subsystem follows a general anomaly-detection workflow:

```text
Network Telemetry
       │
       ▼
Feature Extraction
       │
       ▼
Data Preprocessing
       │
       ▼
Model Training
       │
       ▼
Behavioral Baseline
       │
       ▼
Live Telemetry
       │
       ▼
Anomaly Detection
       │
       ▼
Threat Classification
       │
       ▼
Logging / Alert / Response
```

The training pipeline can be executed independently from the primary monitoring engine.

---

## Prerequisites

The system is primarily designed for **Linux-based security environments**, particularly Kali Linux.

### Operating System

Recommended:

* Kali Linux
* Debian
* Ubuntu
* Other Debian-based Linux distributions

### Required Software

* Python 3.x
* GCC
* G++
* MySQL Server
* Git

### Required Libraries

#### C++

```text
libpcap
```

#### Python

Typical dependencies include:

```text
scikit-learn
pandas
numpy
flask
mysql-connector-python
```

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

---

# Installation & Deployment

## 1. Clone the Repository

```bash
git clone <repository-url>
cd Zero_Context
```

---

## 2. Create a Python Virtual Environment

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Upgrade pip:

```bash
pip install --upgrade pip
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure MySQL

Start the MySQL service:

```bash
sudo systemctl start mysql
```

Check the service:

```bash
sudo systemctl status mysql
```

Create the required database and tables according to the project's database schema.

Database credentials should be supplied through environment variables or another secure configuration mechanism rather than being hard-coded directly into source files.

Example:

```bash
export DB_HOST="localhost"
export DB_USER="your_user"
export DB_PASSWORD="your_password"
export DB_NAME="zero_context"
```

---

## 4. Compile the C++ Sensor

Navigate to the sensor directory:

```bash
cd sensor
```

Compile the sensor:

```bash
g++ -o sensor_daemon sensor_daemon.cpp sensor.cpp -lpcap
```

Return to the project root:

```bash
cd ..
```

Verify the generated executable:

```bash
ls -l sensor/
```

---

## 5. Train the Machine Learning Models

Before starting the full monitoring engine, generate the initial behavioral baseline:

```bash
python3 engine/train_pipeline.py
```

The training pipeline processes collected telemetry and creates the required ML model artifacts.

---

## 6. Start the Sensor

Packet capture may require elevated privileges.

Run:

```bash
sudo ./sensor/sensor_daemon
```

For background execution:

```bash
sudo ./sensor/sensor_daemon &
```

---

## 7. Start the Intelligence Engine

From the project root:

```bash
python3 main.py
```

---

## 8. Start the Dashboard

In a separate terminal:

```bash
python3 dashboard.py
```

The dashboard can then be accessed through the configured local web address and port.

---

# Recommended Startup Sequence

For a clean deployment, start the components in the following order:

```text
1. MySQL
      ↓
2. C++ Sensor
      ↓
3. Python Intelligence Engine
      ↓
4. Web Dashboard
```

Example:

```bash
sudo systemctl start mysql

sudo ./sensor/sensor_daemon &

python3 main.py

python3 dashboard.py
```

---

# Security Considerations

Because the project performs low-level packet capture and interacts with security-sensitive system resources:

* Run the C++ sensor with the minimum privileges required.
* Do not commit database passwords to Git.
* Use environment variables or secure secret management for credentials.
* Restrict access to the monitoring dashboard.
* Protect MySQL credentials.
* Avoid running the entire application as `root` when unnecessary.
* Review generated logs regularly.
* Test defensive mechanisms only on systems and networks you are authorized to monitor.

---

# Troubleshooting

## libpcap Header Not Found

If compilation reports an error similar to:

```text
fatal error: pcap.h: No such file or directory
```

Install the development package:

```bash
sudo apt update
sudo apt install libpcap-dev
```

Then compile again:

```bash
g++ -o sensor_daemon sensor_daemon.cpp sensor.cpp -lpcap
```

---

## Permission Denied During Packet Capture

Packet capture may require additional privileges.

Try:

```bash
sudo ./sensor/sensor_daemon
```

For production deployments, prefer granting only the specific capabilities required by the sensor instead of running the entire application with unrestricted root privileges.

---

## MySQL Connection Problems

Verify that MySQL is running:

```bash
sudo systemctl status mysql
```

Test connectivity:

```bash
mysql -u your_user -p
```

Then verify the database configuration used by the application.

---

# Development Workflow

A typical development workflow is:

```text
Modify Source
     │
     ▼
Compile C++ Sensor
     │
     ▼
Collect Telemetry
     │
     ▼
Train / Update ML Models
     │
     ▼
Run Detection Engine
     │
     ▼
Validate Alerts
     │
     ▼
Inspect Dashboard
     │
     ▼
Review MySQL Logs
```

---

# Future Enhancements

Potential future versions of **Cyber Defensive Engine** can include:

* Advanced deep-learning-based anomaly detection
* Automated threat response
* Firewall integration
* IP reputation analysis
* Threat intelligence feeds
* GeoIP-based visualization
* Attack timeline reconstruction
* Distributed sensor deployment
* Containerized deployment
* REST API integration
* Role-based dashboard authentication
* Alert notification integrations
* Model drift detection
* Continuous/incremental model learning
* SIEM integration
* Enterprise-scale telemetry processing

---

# Project Goals

The primary goals of **Zero_Context** are to provide:

1. Real-time network visibility
2. Intelligent anomaly detection
3. Low-level packet inspection
4. Persistent security event storage
5. Machine-learning-assisted threat detection
6. Centralized security visualization
7. A modular foundation for future defensive security capabilities

---

# Disclaimer

**Zero_Context is intended for authorized defensive security, research, educational, and testing purposes only.**

Do not deploy packet capture, monitoring, automated blocking, or other defensive mechanisms against systems or networks without appropriate authorization.

---

# Author

**Abhinandan**

**B.Tech Computer Science and Engineering**
**Gurukul Kangri Vishwavidyalaya**

---

# License

Add the project's applicable license here, for example:

```text
MIT License
```

or replace this section with the license selected for the repository.
