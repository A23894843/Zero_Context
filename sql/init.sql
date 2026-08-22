CREATE TABLE IF NOT EXISTS threat_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DOUBLE NOT NULL,
    sensor_type VARCHAR(64) NOT NULL,
    anomaly_score FLOAT NOT NULL,
    description TEXT,
    INDEX idx_timestamp (timestamp)
);
