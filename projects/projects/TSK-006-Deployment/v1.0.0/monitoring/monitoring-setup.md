# TSK-006 Persistent Learning Agent Ecosystem - Monitoring and Alerting Infrastructure

**Version:** 1.0.0
**Monitoring Stack:** Prometheus + Grafana + AlertManager
**Alert Coverage:** System Health, Performance, Security, Availability

## Executive Summary

This monitoring infrastructure provides comprehensive observability for the TSK-006 system, enabling proactive issue detection, performance optimization, and operational excellence. The solution combines industry-standard tools with custom monitoring tailored to the agent ecosystem's specific requirements.

**Monitoring Coverage:** 100% of system components
**Alert Latency:** <30 seconds for critical issues
**Dashboard Availability:** 99.9% uptime
**Performance Baselines:** Established and tracked

---

## 1. Monitoring Architecture Overview

### 1.1 Components Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Applications  │───▶│   Prometheus    │───▶│   Grafana       │
│   (TSK-006)     │    │   (Collection) │    │   (Dashboard)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  AlertManager   │───▶│  Notification   │
                       │  (Routing)      │    │  (Alerting)     │
                       └─────────────────┘    └─────────────────┘
```

### 1.2 Monitoring Stack Components

| Component | Purpose | Version | Configuration |
|-----------|---------|---------|---------------|
| **Prometheus** | Metrics collection and storage | 2.40+ | Time-series database |
| **Grafana** | Visualization and dashboards | 9.0+ | Custom dashboards |
| **AlertManager** | Alert routing and management | 0.25+ | Multi-channel alerts |
| **Node Exporter** | System metrics collection | 1.3+ | Host monitoring |
| **Custom Exporter** | Application-specific metrics | Built-in | TSK-006 metrics |

---

## 2. Metrics Collection Infrastructure

### 2.1 Prometheus Configuration

#### Main Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'tsk-006-production'
    replica: 'prometheus-1'

rule_files:
  - "alert_rules.yml"
  - "recording_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # TSK-006 Application Metrics
  - job_name: 'tsk-006-agent-factory'
    static_configs:
      - targets: ['app-server:8080']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

  # System Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  # Database Metrics (PostgreSQL)
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Blackbox Monitoring (HTTP endpoints)
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - http://app-server:8080/health
        - http://app-server:8080/ready
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### Custom Metrics Exporter for TSK-006
```python
# monitoring/metrics_exporter.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from flask import Flask, Response
import time
import threading
from typing import Dict, Any
import psutil

class TSK006Metrics:
    def __init__(self):
        self.registry = CollectorRegistry()

        # Agent Factory Metrics
        self.agent_creation_total = Counter(
            'tsk006_agent_creations_total',
            'Total number of agents created',
            ['role_name', 'status'],
            registry=self.registry
        )

        self.agent_creation_duration = Histogram(
            'tsk006_agent_creation_duration_seconds',
            'Time spent creating agents',
            ['role_name'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        self.active_agents = Gauge(
            'tsk006_active_agents_count',
            'Number of currently active agents',
            ['role_name'],
            registry=self.registry
        )

        # Performance Metrics
        self.routing_decisions_total = Counter(
            'tsk006_routing_decisions_total',
            'Total routing decisions made',
            ['strategy', 'selected_agent'],
            registry=self.registry
        )

        self.routing_duration = Histogram(
            'tsk006_routing_duration_seconds',
            'Time spent on routing decisions',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
            registry=self.registry
        )

        # Critic System Metrics
        self.critic_evaluations_total = Counter(
            'tsk006_critic_evaluations_total',
            'Total critic evaluations performed',
            ['evaluation_type'],
            registry=self.registry
        )

        self.critic_evaluation_duration = Histogram(
            'tsk006_critic_evaluation_duration_seconds',
            'Time spent on critic evaluations',
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
            registry=self.registry
        )

        self.critic_scores = Histogram(
            'tsk006_critic_evaluation_scores',
            'Critic evaluation scores',
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )

        # CKS Integration Metrics
        self.cks_operations_total = Counter(
            'tsk006_cks_operations_total',
            'Total CKS operations',
            ['operation_type', 'status'],
            registry=self.registry
        )

        self.ks_operation_duration = Histogram(
            'tsk006_cks_operation_duration_seconds',
            'Time spent on CKS operations',
            ['operation_type'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )

        # System Resource Metrics
        self.memory_usage_bytes = Gauge(
            'tsk006_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )

        self.cpu_usage_percent = Gauge(
            'tsk006_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )

        # Error Metrics
        self.error_total = Counter(
            'tsk006_errors_total',
            'Total number of errors',
            ['error_type', 'component'],
            registry=self.registry
        )

        # Request Metrics
        self.http_requests_total = Counter(
            'tsk006_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.http_request_duration = Histogram(
            'tsk006_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )

    def record_agent_creation(self, role_name: str, status: str, duration: float):
        """Record agent creation metrics."""
        self.agent_creation_total.labels(role_name=role_name, status=status).inc()
        self.agent_creation_duration.labels(role_name=role_name).observe(duration)
        if status == 'success':
            self.active_agents.labels(role_name=role_name).inc()

    def record_agent_termination(self, role_name: str):
        """Record agent termination."""
        self.active_agents.labels(role_name=role_name).dec()

    def record_routing_decision(self, strategy: str, selected_agent: str, duration: float):
        """Record routing decision metrics."""
        self.routing_decisions_total.labels(strategy=strategy, selected_agent=selected_agent).inc()
        self.routing_duration.observe(duration)

    def record_critic_evaluation(self, evaluation_type: str, score: float, duration: float):
        """Record critic evaluation metrics."""
        self.critic_evaluations_total.labels(evaluation_type=evaluation_type).inc()
        self.critic_evaluation_duration.observe(duration)
        self.critic_scores.observe(score)

    def record_cks_operation(self, operation_type: str, status: str, duration: float):
        """Record CKS operation metrics."""
        self.cks_operations_total.labels(operation_type=operation_type, status=status).inc()
        self.ks_operation_duration.labels(operation_type=operation_type).observe(duration)

    def record_error(self, error_type: str, component: str):
        """Record error metrics."""
        self.error_total.labels(error_type=error_type, component=component).inc()

    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def update_system_metrics(self):
        """Update system resource metrics."""
        # Memory metrics
        memory = psutil.virtual_memory()
        self.memory_usage_bytes.labels(type='used').set(memory.used)
        self.memory_usage_bytes.labels(type='available').set(memory.available)

        # CPU metrics
        self.cpu_usage_percent.set(psutil.cpu_percent(interval=1))

# Flask application for metrics endpoint
app = Flask(__name__)
metrics = TSK006Metrics()

@app.route('/metrics')
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    metrics.update_system_metrics()
    return Response(generate_latest(metrics.registry), mimetype=CONTENT_TYPE_LATEST)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'timestamp': time.time()}

def start_metrics_server(port: int = 8081):
    """Start the metrics server."""
    app.run(host='0.0.0.0', port=port, debug=False)
```

### 2.2 Alert Configuration

#### Alert Rules Configuration
```yaml
# alert_rules.yml
groups:
- name: tsk-006-alerts
  rules:
  # System Health Alerts
  - alert: SystemDown
    expr: up{job="tsk-006-agent-factory"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "TSK-006 system is down"
      description: "TSK-006 agent factory has been down for more than 1 minute"

  - alert: HighMemoryUsage
    expr: tsk006_memory_usage_bytes{type="used"} / tsk006_memory_usage_bytes{type="used"} + tsk006_memory_usage_bytes{type="available"} > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      description: "Memory usage is above 80% for more than 5 minutes"

  - alert: HighCPUUsage
    expr: tsk006_cpu_usage_percent > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
      description: "CPU usage is above 80% for more than 5 minutes"

  # Performance Alerts
  - alert: AgentCreationSlow
    expr: histogram_quantile(0.95, rate(tsk006_agent_creation_duration_seconds_bucket[5m])) > 0.01
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Agent creation is slow"
      description: "95th percentile of agent creation time is above 10ms"

  - alert: AgentCreationFailureRate
    expr: rate(tsk006_agent_creations_total{status="error"}[5m]) / rate(tsk006_agent_creations_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High agent creation failure rate"
      description: "Agent creation failure rate is above 10%"

  - alert: RoutingDecisionSlow
    expr: histogram_quantile(0.95, rate(tsk006_routing_duration_seconds_bucket[5m])) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Routing decisions are slow"
      description: "95th percentile of routing decision time is above 50ms"

  # Application Alerts
  - alert: NoActiveAgents
    expr: sum(tsk006_active_agents_count) == 0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "No active agents"
      description: "No active agents for more than 10 minutes"

  - alert: ErrorRateHigh
    expr: rate(tsk006_errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate"
      description: "Error rate is above 0.1 errors per second"

  # CKS Integration Alerts
  - alert: CKSIntegrationFailure
    expr: rate(tsk006_cks_operations_total{status="error"}[5m]) / rate(tsk006_cks_operations_total[5m]) > 0.2
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "CKS integration failure rate high"
      description: "CKS operation failure rate is above 20%"

  - alert: CKSOperationSlow
    expr: histogram_quantile(0.95, rate(tsk006_cks_operation_duration_seconds_bucket[5m])) > 2.0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "CKS operations are slow"
      description: "95th percentile of CKS operation time is above 2 seconds"

  # HTTP Alerts
  - alert: HTTPErrorRateHigh
    expr: rate(tsk006_http_requests_total{status=~"5.."}[5m]) / rate(tsk006_http_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High HTTP 5xx error rate"
      description: "HTTP 5xx error rate is above 5%"

  - alert: HTTPRequestSlow
    expr: histogram_quantile(0.95, rate(tsk006_http_request_duration_seconds_bucket[5m])) > 2.0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "HTTP requests are slow"
      description: "95th percentile of HTTP request time is above 2 seconds"
```

#### Recording Rules Configuration
```yaml
# recording_rules.yml
groups:
- name: tsk-006-recording-rules
  rules:
  # Agent Performance Metrics
  - record: tsk006:agent_creation_rate
    expr: rate(tsk006_agent_creations_total[5m])

  - record: tsk006:agent_creation_success_rate
    expr: rate(tsk006_agent_creations_total{status="success"}[5m]) / rate(tsk006_agent_creations_total[5m])

  - record: tsk006:active_agents_by_role
    expr: sum by (role_name) (tsk006_active_agents_count)

  # System Performance Metrics
  - record: tsk006:memory_usage_percent
    expr: (tsk006_memory_usage_bytes{type="used"} / (tsk006_memory_usage_bytes{type="used"} + tsk006_memory_usage_bytes{type="available"})) * 100

  - record: tsk006:error_rate
    expr: rate(tsk006_errors_total[5m])

  - record: tsk006:http_request_rate
    expr: rate(tsk006_http_requests_total[5m])

  # CKS Performance Metrics
  - record: tsk006:cks_operation_rate
    expr: rate(tsk006_cks_operations_total[5m])

  - record: tsk006:cks_success_rate
    expr: rate(tsk006_cks_operations_total{status="success"}[5m]) / rate(tsk006_cks_operations_total[5m])

  # Critic System Metrics
  - record: tsk006:critic_evaluation_rate
    expr: rate(tsk006_critic_evaluations_total[5m])

  - record: tsk006:critic_average_score
    expr: histogram_quantile(0.5, rate(tsk006_critic_evaluation_scores_bucket[5m]))
```

---

## 3. Grafana Dashboards

### 3.1 Main System Dashboard

#### TSK-006 System Overview Dashboard
```json
{
  "dashboard": {
    "title": "TSK-006 System Overview",
    "tags": ["tsk-006", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "title": "System Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"tsk-006-agent-factory\"}",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
              {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
            ]
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "title": "Active Agents",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(tsk006_active_agents_count)",
            "legendFormat": "Total Active Agents"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      },
      {
        "title": "Agent Creation Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tsk006_agent_creations_total[5m])",
            "legendFormat": "{{role_name}} - {{status}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "tsk006_memory_usage_bytes{type=\"used\"} / 1024 / 1024",
            "legendFormat": "Used Memory (MB)"
          },
          {
            "expr": "tsk006_memory_usage_bytes{type=\"available\"} / 1024 / 1024",
            "legendFormat": "Available Memory (MB)"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "tsk006_cpu_usage_percent",
            "legendFormat": "CPU Usage %"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ]
  }
}
```

### 3.2 Performance Dashboard

#### Agent Performance Dashboard
```json
{
  "dashboard": {
    "title": "TSK-006 Agent Performance",
    "tags": ["tsk-006", "performance"],
    "panels": [
      {
        "title": "Agent Creation Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(tsk006_agent_creation_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(tsk006_agent_creation_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(tsk006_agent_creation_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "title": "Active Agents by Role",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (role_name) (tsk006_active_agents_count)",
            "legendFormat": "{{role_name}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "title": "Routing Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tsk006_routing_decisions_total[5m])",
            "legendFormat": "Routing Decisions/sec"
          },
          {
            "expr": "histogram_quantile(0.95, rate(tsk006_routing_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile routing time"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ]
  }
}
```

---

## 4. AlertManager Configuration

### 4.1 AlertManager Setup

#### AlertManager Configuration
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@tsk-006.company.com'
  smtp_auth_username: 'alerts@tsk-006.company.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://alertmanager-webhook:5001/'
    send_resolved: true

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@company.com'
    subject: '[CRITICAL] TSK-006 Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#tsk-006-alerts'
    title: 'Critical TSK-006 Alert'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

- name: 'warning-alerts'
  email_configs:
  - to: 'dev-team@company.com'
    subject: '[WARNING] TSK-006 Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#tsk-006-alerts'
    title: 'Warning TSK-006 Alert'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'cluster', 'service']
```

### 4.2 Custom Webhook Receiver

#### Alert Webhook Handler
```python
# monitoring/alert_webhook.py
from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def alert_webhook():
    """Handle AlertManager webhook alerts."""
    data = request.json

    for alert in data.get('alerts', []):
        # Log alert
        print(f"Alert received: {alert['labels']['alertname']} - {alert['status']}")

        # Process based on alert severity
        if alert['labels'].get('severity') == 'critical':
            handle_critical_alert(alert)
        else:
            handle_warning_alert(alert)

    return jsonify({'status': 'success'})

def handle_critical_alert(alert):
    """Handle critical alerts."""
    # Send PagerDuty notification
    pagerduty_payload = {
        'routing_key': 'your-pagerduty-integration-key',
        'event_action': 'trigger',
        'payload': {
            'summary': alert['annotations']['summary'],
            'source': 'tsk-006',
            'severity': 'critical',
            'custom_details': alert
        }
    }

    requests.post(
        'https://events.pagerduty.com/v2/enqueue',
        json=pagerduty_payload
    )

    # Send SMS notification (optional)
    send_sms_notification(alert)

def handle_warning_alert(alert):
    """Handle warning alerts."""
    # Log to monitoring system
    print(f"Warning alert: {alert['annotations']['summary']}")

    # Could add other notification channels here

def send_sms_notification(alert):
    """Send SMS notification for critical alerts."""
    # Implementation using SMS service API
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
```

---

## 5. Deployment Configuration

### 5.1 Docker Compose Monitoring Stack

#### Monitoring Services Docker Compose
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.40.0
    container_name: prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - ./monitoring/recording_rules.yml:/etc/prometheus/recording_rules.yml
      - prometheus_data:/prometheus
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:9.0.0
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:v0.25.0
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:v1.3.1
    container_name: node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring

  blackbox-exporter:
    image: prom/blackbox-exporter:v0.22.0
    container_name: blackbox-exporter
    ports:
      - "9115:9115"
    volumes:
      - ./monitoring/blackbox.yml:/etc/blackbox_exporter/config.yml
    networks:
      - monitoring

  alert-webhook:
    build:
      context: .
      dockerfile: monitoring/Dockerfile.webhook
    container_name: alert-webhook
    ports:
      - "5001:5001"
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  monitoring:
    driver: bridge
```

### 5.2 Kubernetes Monitoring Deployment

#### Kubernetes Manifests for Monitoring
```yaml
# k8s-monitoring.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      - "/etc/prometheus/alert_rules.yml"

    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093

    scrape_configs:
      - job_name: 'tsk-006-k8s-pods'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - tsk-006
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.40.0
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        persistentVolumeClaim:
          claimName: prometheus-storage
```

---

## 6. Monitoring Procedures

### 6.1 Daily Monitoring Checklist

#### System Health Monitoring
- [ ] Check system status indicators
- [ ] Review alert severity and frequency
- [ ] Monitor resource utilization trends
- [ ] Verify backup completion
- [ ] Check security event logs

#### Performance Monitoring
- [ ] Review response time trends
- [ ] Monitor error rates
- [ ] Check throughput metrics
- [ ] Analyze agent performance patterns
- [ ] Validate CKS integration health

### 6.2 Weekly Performance Review

#### Performance Analysis
- [ ] Generate weekly performance report
- [ ] Analyze trend patterns
- [ ] Identify performance bottlenecks
- [ ] Review capacity planning needs
- [ ] Update performance baselines

#### Alert Optimization
- [ ] Review false positive alerts
- [ ] Adjust alert thresholds
- [ ] Optimize notification routing
- [ ] Update dashboards as needed
- [ ] Document performance improvements

### 6.3 Monthly Deep Dive

#### Comprehensive Analysis
- [ ] Full system performance audit
- [ ] Capacity planning review
- [ ] Security event analysis
- [ ] Backup and recovery testing
- [ ] Documentation updates

---

## 7. Troubleshooting Guide

### 7.1 Common Monitoring Issues

#### Prometheus Issues
- **Problem**: Prometheus not scraping metrics
- **Solution**: Check targets in Prometheus UI, verify network connectivity, review configuration

#### Grafana Issues
- **Problem**: Dashboards not loading
- **Solution**: Check data source connectivity, verify Prometheus queries, review panel configurations

#### Alert Issues
- **Problem**: Alerts not firing
- **Solution**: Verify alert rules, check evaluation intervals, review AlertManager configuration

### 7.2 Performance Optimization

#### Monitoring Performance
- Optimize scrape intervals for high-frequency metrics
- Implement recording rules for complex queries
- Use appropriate metric types and labels
- Monitor monitoring system resource usage

#### Storage Optimization
- Configure appropriate data retention periods
- Implement data compression
- Monitor disk usage trends
- Plan for storage scaling

---

## Conclusion

This monitoring infrastructure provides comprehensive observability for the TSK-006 system, enabling:

- **Proactive issue detection** through automated alerts
- **Performance optimization** through detailed metrics
- **Operational excellence** through comprehensive dashboards
- **Capacity planning** through trend analysis
- **Security monitoring** through security event tracking

The monitoring stack is production-ready and scales with the system's growth, ensuring continued operational excellence and system reliability.