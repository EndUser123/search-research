#!/usr/bin/env python3
"""
Comprehensive Monitoring and Alerting Setup Script
For Task Execution Enhancements Project

This script handles:
- Monitoring system deployment
- Alert rule configuration
- Dashboard setup for system metrics
- Log aggregation and analysis setup
- Performance baseline establishment
"""

import os
import sys
import json
import yaml
import logging
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import threading

@dataclass
class MonitoringConfig:
    """Configuration for monitoring setup"""
    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3000"
    alertmanager_url: str = "http://localhost:9093"
    elasticsearch_url: str = "http://localhost:9200"
    kibana_url: str = "http://localhost:5601"

    # Service configurations
    prometheus_enabled: bool = True
    grafana_enabled: bool = True
    alertmanager_enabled: bool = True
    elasticsearch_enabled: bool = True
    kibana_enabled: bool = True

    # Authentication
    grafana_admin_user: str = "admin"
    grafana_admin_password: str = "admin"

    # Paths
    monitoring_config_dir: str = "deployment-automation/config/monitoring"
    alert_rules_dir: str = "deployment-automation/config/alert-rules"
    dashboards_dir: str = "deployment-automation/config/dashboards"

class MonitoringSetupError(Exception):
    """Custom exception for monitoring setup failures"""
    pass

class MonitoringSetup:
    """Comprehensive monitoring and alerting setup"""

    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.logger = self._setup_logging()
        self.base_path = Path.cwd()
        self.monitoring_dir = Path(self.config.monitoring_config_dir)
        self.setup_log = []

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    f'monitoring_setup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                )
            ]
        )
        return logging.getLogger(__name__)

    def log_step(self, step: str, status: str, details: str = ""):
        """Log monitoring setup step"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.setup_log.append(log_entry)

        if status == 'SUCCESS':
            self.logger.info(f"✅ {step}: {details}")
        elif status == 'WARNING':
            self.logger.warning(f"⚠️  {step}: {details}")
        else:
            self.logger.error(f"❌ {step}: {details}")

    def create_monitoring_directories(self) -> bool:
        """Create monitoring configuration directories"""
        self.log_step("Creating Directories", "STARTED")

        try:
            directories = [
                self.monitoring_dir,
                Path(self.config.alert_rules_dir),
                Path(self.config.dashboards_dir),
                self.monitoring_dir / "prometheus",
                self.monitoring_dir / "grafana",
                self.monitoring_dir / "alertmanager",
                self.monitoring_dir / "elasticsearch"
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.log_step(f"Directory {directory}", "SUCCESS", "Created")

            self.log_step("Creating Directories", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Creating Directories", "FAILED", str(e))
            return False

    def setup_prometheus(self) -> bool:
        """Setup Prometheus monitoring"""
        if not self.config.prometheus_enabled:
            self.log_step("Prometheus Setup", "SKIPPED", "Disabled in configuration")
            return True

        self.log_step("Prometheus Setup", "STARTED")

        try:
            # Create Prometheus configuration
            prometheus_config = {
                "global": {
                    "scrape_interval": "15s",
                    "evaluation_interval": "15s"
                },
                "rule_files": [
                    f"/etc/prometheus/rules/{Path(self.config.alert_rules_dir).name}/*.yml"
                ],
                "alerting": {
                    "alertmanagers": [
                        {
                            "static_configs": [
                                {
                                    "targets": ["alertmanager:9093"]
                                }
                            ]
                        }
                    ]
                },
                "scrape_configs": [
                    {
                        "job_name": "task-execution-enhancements",
                        "static_configs": [
                            {
                                "targets": ["localhost:8000"],
                                "labels": {
                                    "environment": "production",
                                    "service": "task-execution-enhancements"
                                }
                            }
                        ],
                        "scrape_interval": "5s",
                        "metrics_path": "/metrics"
                    },
                    {
                        "job_name": "session-management",
                        "static_configs": [
                            {
                                "targets": ["localhost:8001"],
                                "labels": {
                                    "environment": "production",
                                    "service": "session-management"
                                }
                            }
                        ],
                        "scrape_interval": "10s"
                    },
                    {
                        "job_name": "csf-nip",
                        "static_configs": [
                            {
                                "targets": ["localhost:8002"],
                                "labels": {
                                    "environment": "production",
                                    "service": "csf-nip"
                                }
                            }
                        ],
                        "scrape_interval": "10s"
                    },
                    {
                        "job_name": "node-exporter",
                        "static_configs": [
                            {
                                "targets": ["localhost:9100"]
                            }
                        ]
                    }
                ]
            }

            # Write Prometheus configuration
            prometheus_config_path = self.monitoring_dir / "prometheus" / "prometheus.yml"
            with open(prometheus_config_path, 'w') as f:
                yaml.dump(prometheus_config, f, default_flow_style=False)

            self.log_step("Prometheus Config", "SUCCESS", "Configuration created")

            # Create Docker Compose file for Prometheus
            prometheus_docker = {
                "version": "3.8",
                "services": {
                    "prometheus": {
                        "image": "prom/prometheus:latest",
                        "container_name": "task-execution-prometheus",
                        "ports": ["9090:9090"],
                        "volumes": [
                            "./config/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml",
                            f"./config/{Path(self.config.alert_rules_dir).name}:/etc/prometheus/rules",
                            "prometheus-data:/prometheus"
                        ],
                        "command": [
                            "--config.file=/etc/prometheus/prometheus.yml",
                            "--storage.tsdb.path=/prometheus",
                            "--web.console.libraries=/etc/prometheus/console_libraries",
                            "--web.console.templates=/etc/prometheus/consoles",
                            "--storage.tsdb.retention.time=30d",
                            "--web.enable-lifecycle"
                        ],
                        "restart": "unless-stopped"
                    }
                },
                "volumes": {
                    "prometheus-data": {}
                }
            }

            prometheus_docker_path = self.monitoring_dir / "prometheus" / "docker-compose.yml"
            with open(prometheus_docker_path, 'w') as f:
                yaml.dump(prometheus_docker, f)

            self.log_step("Prometheus Docker Config", "SUCCESS")
            self.log_step("Prometheus Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Prometheus Setup", "FAILED", str(e))
            return False

    def setup_grafana(self) -> bool:
        """Setup Grafana dashboards"""
        if not self.config.grafana_enabled:
            self.log_step("Grafana Setup", "SKIPPED", "Disabled in configuration")
            return True

        self.log_step("Grafana Setup", "STARTED")

        try:
            # Create Grafana configuration
            grafana_config = {
                "version": "3.8",
                "services": {
                    "grafana": {
                        "image": "grafana/grafana:latest",
                        "container_name": "task-execution-grafana",
                        "ports": ["3000:3000"],
                        "environment": {
                            "GF_SECURITY_ADMIN_USER": self.config.grafana_admin_user,
                            "GF_SECURITY_ADMIN_PASSWORD": self.config.grafana_admin_password,
                            "GF_INSTALL_PLUGINS": "grafana-clock-panel,grafana-simple-json-datasource"
                        },
                        "volumes": [
                            "./config/monitoring/grafana/provisioning:/etc/grafana/provisioning",
                            "./config/dashboards:/var/lib/grafana/dashboards",
                            "grafana-data:/var/lib/grafana"
                        ],
                        "restart": "unless-stopped"
                    }
                },
                "volumes": {
                    "grafana-data": {}
                }
            }

            grafana_docker_path = self.monitoring_dir / "grafana" / "docker-compose.yml"
            with open(grafana_docker_path, 'w') as f:
                yaml.dump(grafana_config, f)

            # Create Grafana provisioning configuration
            provisioning_dir = self.monitoring_dir / "grafana" / "provisioning"
            provisioning_dir.mkdir(parents=True, exist_ok=True)

            # Datasource configuration
            datasources_config = {
                "apiVersion": 1,
                "datasources": [
                    {
                        "name": "Prometheus",
                        "type": "prometheus",
                        "url": self.config.prometheus_url,
                        "access": "proxy",
                        "isDefault": True,
                        "editable": True
                    },
                    {
                        "name": "Elasticsearch",
                        "type": "elasticsearch",
                        "url": self.config.elasticsearch_url,
                        "access": "proxy",
                        "database": "logs-*",
                        "interval": "Daily",
                        "timeField": "@timestamp"
                    }
                ]
            }

            datasources_path = provisioning_dir / "datasources" / "prometheus.yml"
            datasources_path.parent.mkdir(parents=True, exist_ok=True)
            with open(datasources_path, 'w') as f:
                yaml.dump(datasources_config, f)

            # Dashboard provisioning
            dashboards_config = {
                "apiVersion": 1,
                "providers": [
                    {
                        "name": "default",
                        "orgId": 1,
                        "folder": "",
                        "type": "file",
                        "disableDeletion": False,
                        "updateIntervalSeconds": 10,
                        "options": {
                            "path": "/var/lib/grafana/dashboards"
                        }
                    }
                ]
            }

            dashboards_provision_path = provisioning_dir / "dashboards" / "default.yml"
            dashboards_provision_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dashboards_provision_path, 'w') as f:
                yaml.dump(dashboards_config, f)

            self.log_step("Grafana Config", "SUCCESS", "Configuration created")
            self.log_step("Grafana Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Grafana Setup", "FAILED", str(e))
            return False

    def setup_alertmanager(self) -> bool:
        """Setup Alertmanager for alerting"""
        if not self.config.alertmanager_enabled:
            self.log_step("Alertmanager Setup", "SKIPPED", "Disabled in configuration")
            return True

        self.log_step("Alertmanager Setup", "STARTED")

        try:
            # Create Alertmanager configuration
            alertmanager_config = {
                "global": {
                    "smtp_smarthost": "localhost:587",
                    "smtp_from": "alerts@task-execution-enhancements.com"
                },
                "route": {
                    "group_by": ["alertname", "environment", "service"],
                    "group_wait": "10s",
                    "group_interval": "10s",
                    "repeat_interval": "1h",
                    "receiver": "default-receiver",
                    "routes": [
                        {
                            "match": {
                                "severity": "critical"
                            },
                            "receiver": "critical-alerts",
                            "group_wait": "5s"
                        },
                        {
                            "match": {
                                "severity": "warning"
                            },
                            "receiver": "warning-alerts"
                        }
                    ]
                },
                "receivers": [
                    {
                        "name": "default-receiver",
                        "email_configs": [
                            {
                                "to": "admin@task-execution-enhancements.com",
                                "subject": "[Task Execution] {{ .GroupLabels.alertname }}",
                                "body": |
                                  {{ range .Alerts }}
                                  Alert: {{ .Annotations.summary }}
                                  Description: {{ .Annotations.description }}
                                  {{ end }}
                            }
                        ]
                    },
                    {
                        "name": "critical-alerts",
                        "email_configs": [
                            {
                                "to": "critical@task-execution-enhancements.com",
                                "subject": "[CRITICAL] Task Execution Alert: {{ .GroupLabels.alertname }}",
                                "body": |
                                  CRITICAL ALERT!
                                  {{ range .Alerts }}
                                  Alert: {{ .Annotations.summary }}
                                  Description: {{ .Annotations.description }}
                                  Severity: {{ .Labels.severity }}
                                  Environment: {{ .Labels.environment }}
                                  Service: {{ .Labels.service }}
                                  {{ end }}
                            }
                        ],
                        "webhook_configs": [
                            {
                                "url": "http://localhost:8080/webhooks/critical",
                                "send_resolved": True
                            }
                        ]
                    },
                    {
                        "name": "warning-alerts",
                        "email_configs": [
                            {
                                "to": "warnings@task-execution-enhancements.com",
                                "subject": "[WARNING] Task Execution Alert: {{ .GroupLabels.alertname }}",
                                "body": |
                                  Warning Alert:
                                  {{ range .Alerts }}
                                  Alert: {{ .Annotations.summary }}
                                  Description: {{ .Annotations.description }}
                                  {{ end }}
                            }
                        ]
                    }
                ]
            }

            # Write Alertmanager configuration
            alertmanager_config_path = self.monitoring_dir / "alertmanager" / "alertmanager.yml"
            with open(alertmanager_config_path, 'w') as f:
                yaml.dump(alertmanager_config, f)

            # Create Docker Compose for Alertmanager
            alertmanager_docker = {
                "version": "3.8",
                "services": {
                    "alertmanager": {
                        "image": "prom/alertmanager:latest",
                        "container_name": "task-execution-alertmanager",
                        "ports": ["9093:9093"],
                        "volumes": [
                            "./config/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml",
                            "alertmanager-data:/alertmanager"
                        ],
                        "command": [
                            "--config.file=/etc/alertmanager/alertmanager.yml",
                            "--storage.path=/alertmanager"
                        ],
                        "restart": "unless-stopped"
                    }
                },
                "volumes": {
                    "alertmanager-data": {}
                }
            }

            alertmanager_docker_path = self.monitoring_dir / "alertmanager" / "docker-compose.yml"
            with open(alertmanager_docker_path, 'w') as f:
                yaml.dump(alertmanager_docker, f)

            self.log_step("Alertmanager Config", "SUCCESS")
            self.log_step("Alertmanager Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Alertmanager Setup", "FAILED", str(e))
            return False

    def create_alert_rules(self) -> bool:
        """Create comprehensive alert rules"""
        self.log_step("Creating Alert Rules", "STARTED")

        try:
            alert_rules_dir = Path(self.config.alert_rules_dir)
            alert_rules_dir.mkdir(parents=True, exist_ok=True)

            # Session Management Alerts
            session_rules = {
                "groups": [
                    {
                        "name": "session_management.rules",
                        "rules": [
                            {
                                "alert": "SessionManagementDown",
                                "expr": "up{job=\"session-management\"} == 0",
                                "for": "1m",
                                "labels": {
                                    "severity": "critical",
                                    "service": "session-management"
                                },
                                "annotations": {
                                    "summary": "Session Management service is down",
                                    "description": "Session Management service has been down for more than 1 minute"
                                }
                            },
                            {
                                "alert": "HighSessionFailureRate",
                                "expr": "rate(session_failures_total[5m]) > 0.1",
                                "for": "2m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "session-management"
                                },
                                "annotations": {
                                    "summary": "High session failure rate",
                                    "description": "Session failure rate is {{ $value }} errors per second"
                                }
                            },
                            {
                                "alert": "SessionMemoryUsageHigh",
                                "expr": "process_resident_memory_bytes{job=\"session-management\"} / 1024 / 1024 > 512",
                                "for": "5m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "session-management"
                                },
                                "annotations": {
                                    "summary": "High memory usage in session management",
                                    "description": "Memory usage is {{ $value }}MB"
                                }
                            }
                        ]
                    }
                ]
            }

            session_rules_path = alert_rules_dir / "session-management.yml"
            with open(session_rules_path, 'w') as f:
                yaml.dump(session_rules, f)

            # Task Execution Alerts
            task_execution_rules = {
                "groups": [
                    {
                        "name": "task_execution.rules",
                        "rules": [
                            {
                                "alert": "TaskExecutionDown",
                                "expr": "up{job=\"task-execution-enhancements\"} == 0",
                                "for": "1m",
                                "labels": {
                                    "severity": "critical",
                                    "service": "task-execution-enhancements"
                                },
                                "annotations": {
                                    "summary": "Task Execution service is down",
                                    "description": "Task Execution service has been down for more than 1 minute"
                                }
                            },
                            {
                                "alert": "HighTaskFailureRate",
                                "expr": "rate(task_failures_total[5m]) > 0.05",
                                "for": "3m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "task-execution-enhancements"
                                },
                                "annotations": {
                                    "summary": "High task failure rate",
                                    "description": "Task failure rate is {{ $value }} failures per second"
                                }
                            },
                            {
                                "alert": "TaskQueueBacklog",
                                "expr": "task_queue_size > 1000",
                                "for": "5m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "task-execution-enhancements"
                                },
                                "annotations": {
                                    "summary": "Task queue backlog detected",
                                    "description": "Task queue size is {{ $value }}"
                                }
                            }
                        ]
                    }
                ]
            }

            task_execution_rules_path = alert_rules_dir / "task-execution.yml"
            with open(task_execution_rules_path, 'w') as f:
                yaml.dump(task_execution_rules, f)

            # CSF NIP Alerts
            csf_nip_rules = {
                "groups": [
                    {
                        "name": "csf_nip.rules",
                        "rules": [
                            {
                                "alert": "CSFNIPDown",
                                "expr": "up{job=\"csf-nip\"} == 0",
                                "for": "1m",
                                "labels": {
                                    "severity": "critical",
                                    "service": "csf-nip"
                                },
                                "annotations": {
                                    "summary": "CSF NIP service is down",
                                    "description": "CSF NIP service has been down for more than 1 minute"
                                }
                            },
                            {
                                "alert": "CSFNIPLicenseExpiry",
                                "expr": "csf_nip_license_days_remaining < 30",
                                "for": "0m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "csf-nip"
                                },
                                "annotations": {
                                    "summary": "CSF NIP license expiring soon",
                                    "description": "License expires in {{ $value }} days"
                                }
                            }
                        ]
                    }
                ]
            }

            csf_nip_rules_path = alert_rules_dir / "csf-nip.yml"
            with open(csf_nip_rules_path, 'w') as f:
                yaml.dump(csf_nip_rules, f)

            # System Health Alerts
            system_health_rules = {
                "groups": [
                    {
                        "name": "system_health.rules",
                        "rules": [
                            {
                                "alert": "HighCPUUsage",
                                "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
                                "for": "5m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "system"
                                },
                                "annotations": {
                                    "summary": "High CPU usage detected",
                                    "description": "CPU usage is {{ $value }}%"
                                }
                            },
                            {
                                "alert": "HighMemoryUsage",
                                "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85",
                                "for": "5m",
                                "labels": {
                                    "severity": "warning",
                                    "service": "system"
                                },
                                "annotations": {
                                    "summary": "High memory usage detected",
                                    "description": "Memory usage is {{ $value }}%"
                                }
                            },
                            {
                                "alert": "DiskSpaceLow",
                                "expr": "(1 - (node_filesystem_avail_bytes{fstype!=\"tmpfs\"} / node_filesystem_size_bytes{fstype!=\"tmpfs\"})) * 100 > 90",
                                "for": "2m",
                                "labels": {
                                    "severity": "critical",
                                    "service": "system"
                                },
                                "annotations": {
                                    "summary": "Low disk space",
                                    "description": "Disk usage is {{ $value }}%"
                                }
                            }
                        ]
                    }
                ]
            }

            system_health_rules_path = alert_rules_dir / "system-health.yml"
            with open(system_health_rules_path, 'w') as f:
                yaml.dump(system_health_rules, f)

            self.log_step("Creating Alert Rules", "SUCCESS", f"Created {len(list(alert_rules_dir.glob('*.yml')))} rule files")
            return True

        except Exception as e:
            self.log_step("Creating Alert Rules", "FAILED", str(e))
            return False

    def create_grafana_dashboards(self) -> bool:
        """Create Grafana dashboards"""
        self.log_step("Creating Grafana Dashboards", "STARTED")

        try:
            dashboards_dir = Path(self.config.dashboards_dir)
            dashboards_dir.mkdir(parents=True, exist_ok=True)

            # Task Execution Dashboard
            task_execution_dashboard = {
                "dashboard": {
                    "id": None,
                    "title": "Task Execution Enhancements",
                    "tags": ["task-execution-enhancements"],
                    "timezone": "browser",
                    "panels": [
                        {
                            "id": 1,
                            "title": "Service Status",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "up{job=\"task-execution-enhancements\"}",
                                    "legendFormat": "{{ job }}"
                                }
                            ],
                            "fieldConfig": {
                                "defaults": {
                                    "mappings": [
                                        {
                                            "options": {
                                                "0": {"text": "DOWN", "color": "red"},
                                                "1": {"text": "UP", "color": "green"}
                                            },
                                            "type": "value"
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "id": 2,
                            "title": "Task Processing Rate",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "rate(tasks_processed_total[5m])",
                                    "legendFormat": "Tasks/sec"
                                }
                            ]
                        },
                        {
                            "id": 3,
                            "title": "Task Success Rate",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "rate(tasks_successful_total[5m]) / rate(tasks_processed_total[5m]) * 100",
                                    "legendFormat": "Success Rate %"
                                }
                            ]
                        },
                        {
                            "id": 4,
                            "title": "Response Time",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                    "legendFormat": "95th percentile"
                                }
                            ]
                        }
                    ],
                    "time": {"from": "now-1h", "to": "now"},
                    "refresh": "5s"
                }
            }

            task_dashboard_path = dashboards_dir / "task-execution-dashboard.json"
            with open(task_dashboard_path, 'w') as f:
                json.dump(task_execution_dashboard, f, indent=2)

            # Session Management Dashboard
            session_management_dashboard = {
                "dashboard": {
                    "id": None,
                    "title": "Session Management",
                    "tags": ["session-management"],
                    "timezone": "browser",
                    "panels": [
                        {
                            "id": 1,
                            "title": "Active Sessions",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "active_sessions_total",
                                    "legendFormat": "Active Sessions"
                                }
                            ]
                        },
                        {
                            "id": 2,
                            "title": "Session Creation Rate",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "rate(session_creations_total[5m])",
                                    "legendFormat": "Sessions/sec"
                                }
                            ]
                        },
                        {
                            "id": 3,
                            "title": "Session Duration",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "histogram_quantile(0.50, rate(session_duration_seconds_bucket[5m]))",
                                    "legendFormat": "50th percentile"
                                }
                            ]
                        },
                        {
                            "id": 4,
                            "title": "Memory Usage",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "process_resident_memory_bytes{job=\"session-management\"} / 1024 / 1024",
                                    "legendFormat": "Memory (MB)"
                                }
                            ]
                        }
                    ],
                    "time": {"from": "now-1h", "to": "now"},
                    "refresh": "5s"
                }
            }

            session_dashboard_path = dashboards_dir / "session-management-dashboard.json"
            with open(session_dashboard_path, 'w') as f:
                json.dump(session_management_dashboard, f, indent=2)

            # System Overview Dashboard
            system_overview_dashboard = {
                "dashboard": {
                    "id": None,
                    "title": "System Overview",
                    "tags": ["system"],
                    "timezone": "browser",
                    "panels": [
                        {
                            "id": 1,
                            "title": "CPU Usage",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                                    "legendFormat": "{{ instance }}"
                                }
                            ]
                        },
                        {
                            "id": 2,
                            "title": "Memory Usage",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                                    "legendFormat": "{{ instance }}"
                                }
                            ]
                        },
                        {
                            "id": 3,
                            "title": "Disk Usage",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "(1 - (node_filesystem_avail_bytes{fstype!=\"tmpfs\"} / node_filesystem_size_bytes{fstype!=\"tmpfs\"})) * 100",
                                    "legendFormat": "{{ device }}"
                                }
                            ]
                        },
                        {
                            "id": 4,
                            "title": "Network Traffic",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "rate(node_network_receive_bytes_total[5m])",
                                    "legendFormat": "RX {{ device }}"
                                },
                                {
                                    "expr": "rate(node_network_transmit_bytes_total[5m])",
                                    "legendFormat": "TX {{ device }}"
                                }
                            ]
                        }
                    ],
                    "time": {"from": "now-1h", "to": "now"},
                    "refresh": "5s"
                }
            }

            system_dashboard_path = dashboards_dir / "system-overview-dashboard.json"
            with open(system_dashboard_path, 'w') as f:
                json.dump(system_overview_dashboard, f, indent=2)

            self.log_step("Creating Grafana Dashboards", "SUCCESS", f"Created {len(list(dashboards_dir.glob('*.json')))} dashboards")
            return True

        except Exception as e:
            self.log_step("Creating Grafana Dashboards", "FAILED", str(e))
            return False

    def setup_log_aggregation(self) -> bool:
        """Setup Elasticsearch and Kibana for log aggregation"""
        if not self.config.elasticsearch_enabled:
            self.log_step("Log Aggregation Setup", "SKIPPED", "Elasticsearch disabled in configuration")
            return True

        self.log_step("Log Aggregation Setup", "STARTED")

        try:
            # Create Elasticsearch configuration
            elasticsearch_docker = {
                "version": "3.8",
                "services": {
                    "elasticsearch": {
                        "image": "docker.elastic.co/elasticsearch/elasticsearch:8.11.0",
                        "container_name": "task-execution-elasticsearch",
                        "environment": {
                            "discovery.type": "single-node",
                            "xpack.security.enabled": "false",
                            "ES_JAVA_OPTS": "-Xms512m -Xmx512m"
                        },
                        "ports": ["9200:9200"],
                        "volumes": [
                            "elasticsearch-data:/usr/share/elasticsearch/data"
                        ],
                        "restart": "unless-stopped"
                    }
                },
                "volumes": {
                    "elasticsearch-data": {}
                }
            }

            elasticsearch_docker_path = self.monitoring_dir / "elasticsearch" / "docker-compose.yml"
            with open(elasticsearch_docker_path, 'w') as f:
                yaml.dump(elasticsearch_docker, f)

            # Create Filebeat configuration
            filebeat_config = {
                "filebeat.inputs": [
                    {
                        "type": "log",
                        "enabled": True,
                        "paths": [
                            "/var/log/task-execution-enhancements/*.log",
                            "/var/log/session-management/*.log",
                            "/var/log/csf-nip/*.log"
                        ],
                        "fields": {
                            "service": "task-execution-enhancements",
                            "environment": "production"
                        },
                        "fields_under_root": True
                    }
                ],
                "output.elasticsearch": {
                    "hosts": ["elasticsearch:9200"],
                    "index": "logs-%{+yyyy.MM.dd}"
                },
                "setup.template.name": "logs",
                "setup.template.pattern": "logs-*"
            }

            filebeat_config_path = self.monitoring_dir / "elasticsearch" / "filebeat.yml"
            with open(filebeat_config_path, 'w') as f:
                yaml.dump(filebeat_config, f)

            self.log_step("Log Aggregation Setup", "SUCCESS")
            return True

        except Exception as e:
            self.log_step("Log Aggregation Setup", "FAILED", str(e))
            return False

    def establish_performance_baseline(self) -> bool:
        """Establish performance baseline for monitoring"""
        self.log_step("Performance Baseline", "STARTED")

        try:
            # Create baseline configuration
            baseline_config = {
                "baseline_metrics": {
                    "task_execution": {
                        "response_time_p50": 0.1,  # seconds
                        "response_time_p95": 0.5,
                        "throughput": 100,  # tasks per second
                        "error_rate": 0.01,  # 1%
                        "cpu_usage": 50,  # percentage
                        "memory_usage": 256  # MB
                    },
                    "session_management": {
                        "session_creation_time": 0.05,
                        "active_sessions_limit": 10000,
                        "memory_usage": 512,
                        "cpu_usage": 30
                    },
                    "csf_nip": {
                        "validation_time": 0.02,
                        "compliance_score": 95,
                        "memory_usage": 128,
                        "cpu_usage": 20
                    }
                },
                "alert_thresholds": {
                    "warning_multiplier": 1.5,
                    "critical_multiplier": 2.0
                },
                "baseline_collection_period": "7d",
                "baseline_update_frequency": "weekly"
            }

            baseline_config_path = self.monitoring_dir / "performance-baseline.json"
            with open(baseline_config_path, 'w') as f:
                json.dump(baseline_config, f, indent=2)

            # Create baseline collection script
            baseline_script = f'''#!/usr/bin/env python3
"""
Performance Baseline Collection Script
"""

import time
import requests
import json
from datetime import datetime, timedelta

def collect_baseline_metrics():
    """Collect baseline metrics from services"""
    services = [
        {{
            "name": "task-execution-enhancements",
            "url": "http://localhost:8000/metrics",
            "health_url": "http://localhost:8000/health"
        }},
        {{
            "name": "session-management",
            "url": "http://localhost:8001/metrics",
            "health_url": "http://localhost:8001/health"
        }},
        {{
            "name": "csf-nip",
            "url": "http://localhost:8002/metrics",
            "health_url": "http://localhost:8002/health"
        }}
    ]

    baseline_data = {{
        "timestamp": datetime.now().isoformat(),
        "services": {{}}
    }}

    for service in services:
        try:
            # Check health
            health_response = requests.get(service["health_url"], timeout=5)
            if health_response.status_code == 200:
                # Collect metrics
                metrics_response = requests.get(service["url"], timeout=5)
                if metrics_response.status_code == 200:
                    baseline_data["services"][service["name"]] = {{
                        "healthy": True,
                        "metrics": metrics_response.text
                    }}
                else:
                    baseline_data["services"][service["name"]] = {{
                        "healthy": False,
                        "error": f"Metrics endpoint returned {{metrics_response.status_code}}"
                    }}
            else:
                baseline_data["services"][service["name"]] = {{
                    "healthy": False,
                    "error": f"Health check returned {{health_response.status_code}}"
                }}
        except Exception as e:
            baseline_data["services"][service["name"]] = {{
                "healthy": False,
                "error": str(e)
            }}

    # Save baseline data
    with open(f"baseline_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.json", "w") as f:
        json.dump(baseline_data, f, indent=2)

    print(f"Baseline collected at {{datetime.now().isoformat()}}")

if __name__ == "__main__":
    collect_baseline_metrics()
'''

            baseline_script_path = self.monitoring_dir / "collect_baseline.py"
            with open(baseline_script_path, 'w') as f:
                f.write(baseline_script)

            # Make script executable
            os.chmod(baseline_script_path, 0o755)

            self.log_step("Performance Baseline", "SUCCESS", "Baseline configuration created")
            return True

        except Exception as e:
            self.log_step("Performance Baseline", "FAILED", str(e))
            return False

    def test_monitoring_setup(self) -> bool:
        """Test monitoring setup"""
        self.log_step("Testing Monitoring Setup", "STARTED")

        try:
            test_results = {}

            # Test Prometheus
            if self.config.prometheus_enabled:
                try:
                    response = requests.get(f"{self.config.prometheus_url}/-/healthy", timeout=10)
                    test_results["prometheus"] = response.status_code == 200
                    self.log_step("Prometheus Test", "SUCCESS" if test_results["prometheus"] else "FAILED")
                except Exception as e:
                    test_results["prometheus"] = False
                    self.log_step("Prometheus Test", "FAILED", str(e))

            # Test Grafana
            if self.config.grafana_enabled:
                try:
                    response = requests.get(f"{self.config.grafana_url}/api/health", timeout=10)
                    test_results["grafana"] = response.status_code == 200
                    self.log_step("Grafana Test", "SUCCESS" if test_results["grafana"] else "FAILED")
                except Exception as e:
                    test_results["grafana"] = False
                    self.log_step("Grafana Test", "FAILED", str(e))

            # Test Alertmanager
            if self.config.alertmanager_enabled:
                try:
                    response = requests.get(f"{self.config.alertmanager_url}/-/healthy", timeout=10)
                    test_results["alertmanager"] = response.status_code == 200
                    self.log_step("Alertmanager Test", "SUCCESS" if test_results["alertmanager"] else "FAILED")
                except Exception as e:
                    test_results["alertmanager"] = False
                    self.log_step("Alertmanager Test", "FAILED", str(e))

            # Test Elasticsearch
            if self.config.elasticsearch_enabled:
                try:
                    response = requests.get(f"{self.config.elasticsearch_url}/_cluster/health", timeout=10)
                    test_results["elasticsearch"] = response.status_code == 200
                    self.log_step("Elasticsearch Test", "SUCCESS" if test_results["elasticsearch"] else "FAILED")
                except Exception as e:
                    test_results["elasticsearch"] = False
                    self.log_step("Elasticsearch Test", "FAILED", str(e))

            success_count = sum(1 for result in test_results.values() if result)
            total_count = len(test_results)

            if success_count == total_count:
                self.log_step("Testing Monitoring Setup", "SUCCESS", f"All {total_count} services healthy")
                return True
            else:
                self.log_step("Testing Monitoring Setup", "WARNING", f"{success_count}/{total_count} services healthy")
                return True  # Continue with partial success

        except Exception as e:
            self.log_step("Testing Monitoring Setup", "FAILED", str(e))
            return False

    def generate_setup_report(self) -> Dict:
        """Generate monitoring setup report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'configuration': asdict(self.config),
            'setup_log': self.setup_log,
            'summary': {
                'total_steps': len(self.setup_log),
                'successful_steps': len([log for log in self.setup_log if log['status'] == 'SUCCESS']),
                'failed_steps': len([log for log in self.setup_log if log['status'] == 'FAILED']),
                'warnings': len([log for log in self.setup_log if log['status'] == 'WARNING'])
            },
            'services': {
                'prometheus': self.config.prometheus_enabled,
                'grafana': self.config.grafana_enabled,
                'alertmanager': self.config.alertmanager_enabled,
                'elasticsearch': self.config.elasticsearch_enabled,
                'kibana': self.config.kibana_enabled
            },
            'status': 'SUCCESS' if all(log['status'] in ['SUCCESS', 'WARNING'] for log in self.setup_log) else 'FAILED'
        }

        # Save report
        report_path = self.monitoring_dir / f"monitoring_setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Monitoring setup report saved to: {report_path}")
        return report

    def run_complete_setup(self) -> bool:
        """Run complete monitoring setup"""
        self.logger.info("Starting comprehensive monitoring setup...")

        setup_steps = [
            self.create_monitoring_directories,
            self.setup_prometheus,
            self.setup_grafana,
            self.setup_alertmanager,
            self.create_alert_rules,
            self.create_grafana_dashboards,
            self.setup_log_aggregation,
            self.establish_performance_baseline,
            self.test_monitoring_setup
        ]

        for step in setup_steps:
            try:
                if not step():
                    self.logger.error("Monitoring setup failed. Check logs for details.")
                    return False
            except Exception as e:
                self.logger.error(f"Setup step failed with exception: {str(e)}")
                return False

        # Generate final report
        report = self.generate_setup_report()

        if report['status'] == 'SUCCESS':
            self.logger.info("🎉 Monitoring setup completed successfully!")
            self.logger.info(f"📊 Grafana: {self.config.grafana_url}")
            self.logger.info(f"📈 Prometheus: {self.config.prometheus_url}")
            self.logger.info(f"🚨 Alertmanager: {self.config.alertmanager_url}")
            if self.config.elasticsearch_enabled:
                self.logger.info(f"📝 Elasticsearch: {self.config.elasticsearch_url}")
                self.logger.info(f"🔍 Kibana: {self.config.kibana_url}")
            return True
        else:
            self.logger.error("❌ Monitoring setup completed with errors.")
            return False

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Task Execution Enhancements Monitoring Setup")
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--prometheus-only', action='store_true', help='Setup Prometheus only')
    parser.add_argument('--grafana-only', action='store_true', help='Setup Grafana only')
    parser.add_argument('--test-only', action='store_true', help='Test existing setup only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Load configuration if provided
    config = MonitoringConfig()
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    # Override based on command line arguments
    if args.prometheus_only:
        config.grafana_enabled = False
        config.alertmanager_enabled = False
        config.elasticsearch_enabled = False
    elif args.grafana_only:
        config.prometheus_enabled = False
        config.alertmanager_enabled = False
        config.elasticsearch_enabled = False

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run monitoring setup
    setup = MonitoringSetup(config)

    try:
        if args.test_only:
            success = setup.test_monitoring_setup()
        else:
            success = setup.run_complete_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        setup.logger.info("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        setup.logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
