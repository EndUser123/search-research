"""Advanced Security Analysis Plugin - Example of enhanced plugin capabilities."""

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from ..data_models import ChunkInfo, LogEntry
from .base import BaseChunkingPlugin

logger = logging.getLogger(__name__)


class SecurityAnalysisPlugin(BaseChunkingPlugin):
    """Advanced security analysis plugin demonstrating enhanced plugin capabilities.

    This plugin showcases the new analyze_chunks method and provides comprehensive
    security analysis including threat detection, anomaly identification, and
    security metrics calculation.
    """

    name = "security_analysis"
    version = "2.0.0"
    dependencies = []  # No external dependencies for this example

    def __init__(self):
        super().__init__()
        self.security_patterns = self._initialize_security_patterns()
        self.threat_indicators = self._initialize_threat_indicators()

    def _initialize_security_patterns(self) -> dict[str, list[str]]:
        """Initialize security-related regex patterns."""
        return {
            "authentication_failure": [
                r"(?i)(authentication|login|auth)\s+(failed|failure|denied|error)",
                r"(?i)(invalid|incorrect|wrong)\s+(password|credentials|login)",
                r"(?i)(access\s+denied|unauthorized|forbidden)",
                r"(?i)(failed\s+login|login\s+failed)",
            ],
            "privilege_escalation": [
                r"(?i)(privilege|permission)\s+(escalation|elevation)",
                r"(?i)(sudo|su|admin|root)\s+(access|granted|denied)",
                r"(?i)(elevated|administrator)\s+(privileges|rights)",
            ],
            "network_intrusion": [
                r"(?i)(intrusion|penetration)\s+(detected|attempt)",
                r"(?i)(suspicious|malicious)\s+(traffic|connection|activity)",
                r"(?i)(port\s+scan|network\s+scan)",
                r"(?i)(brute\s+force|ddos|dos)\s+(attack|attempt)",
            ],
            "malware_detection": [
                r"(?i)(virus|malware|trojan|worm)\s+(detected|found|quarantined)",
                r"(?i)(suspicious\s+file|infected\s+file)",
                r"(?i)(antivirus|security\s+scan)",
            ],
            "data_exfiltration": [
                r"(?i)(data\s+exfiltration|data\s+theft)",
                r"(?i)(unauthorized\s+download|suspicious\s+transfer)",
                r"(?i)(large\s+file\s+transfer|bulk\s+download)",
            ],
            "system_compromise": [
                r"(?i)(system\s+compromise|security\s+breach)",
                r"(?i)(backdoor|rootkit)\s+(detected|installed)",
                r"(?i)(command\s+injection|code\s+injection)",
            ],
        }

    def _initialize_threat_indicators(self) -> dict[str, list[str]]:
        """Initialize threat level indicators."""
        return {
            "critical": [
                "system compromise",
                "data exfiltration",
                "privilege escalation",
                "backdoor",
                "rootkit",
                "security breach",
            ],
            "high": [
                "intrusion detected",
                "malware detected",
                "brute force",
                "unauthorized access",
                "suspicious activity",
            ],
            "medium": [
                "authentication failure",
                "access denied",
                "failed login",
                "suspicious traffic",
                "port scan",
            ],
            "low": ["security scan", "antivirus", "firewall block"],
        }

    def find_boundaries(self, text: str, log_entries: list[LogEntry]) -> list[int]:
        """Find boundaries based on security event clustering."""
        if not log_entries:
            return []

        boundaries = []
        security_events = []

        # Identify security-related log entries
        for i, entry in enumerate(log_entries):
            if self._is_security_related(entry.original_line):
                security_events.append(i)

        if not security_events:
            return []

        # Create boundaries around clusters of security events
        for i in range(len(security_events) - 1):
            current_event = security_events[i]
            next_event = security_events[i + 1]

            # If there's a significant gap between security events, create a boundary
            if next_event - current_event > 10:  # More than 10 lines apart
                boundaries.append(next_event)

        return boundaries

    def score_chunk(self, chunk: str, info: ChunkInfo) -> float:
        """Score chunk based on security relevance and threat level."""
        if not chunk.strip():
            return 0.0

        lines = chunk.split("\n")
        security_score = 0.0
        total_lines = len([line for line in lines if line.strip()])

        if total_lines == 0:
            return 0.0

        security_lines = 0
        threat_level_scores = {"critical": 1.0, "high": 0.8, "medium": 0.6, "low": 0.4}

        for line in lines:
            if line.strip() and self._is_security_related(line):
                security_lines += 1
                threat_level = self._assess_threat_level(line)
                security_score += threat_level_scores.get(threat_level, 0.2)

        if security_lines == 0:
            return 0.1  # Low score for non-security chunks

        # Normalize score: (security_relevance * threat_severity) / total_lines
        relevance_ratio = security_lines / total_lines
        avg_threat_score = security_score / security_lines

        return min(1.0, relevance_ratio * avg_threat_score)

    def analyze_chunks(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """Perform comprehensive security analysis on chunks.

        This method demonstrates the enhanced plugin capabilities by providing
        structured security analysis including threat detection, metrics, and recommendations.
        """
        if not chunks:
            return {}

        analysis_results = {
            "security_summary": self._generate_security_summary(chunks),
            "threat_analysis": self._analyze_threats(chunks),
            "security_metrics": self._calculate_security_metrics(chunks),
            "anomaly_detection": self._detect_security_anomalies(chunks),
            "recommendations": self._generate_security_recommendations(chunks),
            "timeline_analysis": self._analyze_security_timeline(chunks),
            "attack_patterns": self._identify_attack_patterns(chunks),
        }

        return analysis_results

    def _is_security_related(self, line: str) -> bool:
        """Check if a log line is security-related."""
        line_lower = line.lower()

        # Check against all security patterns
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line):
                    return True

        # Additional keyword-based detection
        security_keywords = [
            "security",
            "auth",
            "login",
            "access",
            "denied",
            "failed",
            "unauthorized",
            "forbidden",
            "intrusion",
            "attack",
            "threat",
            "malware",
            "virus",
            "suspicious",
            "breach",
            "compromise",
        ]

        return any(keyword in line_lower for keyword in security_keywords)

    def _assess_threat_level(self, line: str) -> str:
        """Assess the threat level of a security event."""
        line_lower = line.lower()

        for level, indicators in self.threat_indicators.items():
            for indicator in indicators:
                if indicator in line_lower:
                    return level

        return "low"  # Default threat level

    def _generate_security_summary(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> dict[str, Any]:
        """Generate high-level security summary."""
        total_chunks = len(chunks)
        security_chunks = 0
        threat_levels = Counter()
        security_categories = Counter()

        for chunk_text, chunk_info in chunks:
            if self.score_chunk(chunk_text, chunk_info) > 0.1:
                security_chunks += 1

                # Analyze threat levels in this chunk
                for line in chunk_text.split("\n"):
                    if line.strip() and self._is_security_related(line):
                        threat_level = self._assess_threat_level(line)
                        threat_levels[threat_level] += 1

                        # Categorize security events
                        for category, patterns in self.security_patterns.items():
                            for pattern in patterns:
                                if re.search(pattern, line):
                                    security_categories[category] += 1
                                    break

        return {
            "total_chunks_analyzed": total_chunks,
            "security_relevant_chunks": security_chunks,
            "security_coverage_percentage": (security_chunks / total_chunks * 100)
            if total_chunks > 0
            else 0,
            "threat_level_distribution": dict(threat_levels),
            "security_event_categories": dict(security_categories),
            "overall_risk_level": self._calculate_overall_risk(threat_levels),
        }

    def _analyze_threats(self, chunks: list[tuple[str, ChunkInfo]]) -> dict[str, Any]:
        """Analyze specific threats found in the logs."""
        threats = []
        threat_patterns = defaultdict(list)

        for chunk_text, chunk_info in chunks:
            lines = chunk_text.split("\n")
            for line_num, line in enumerate(lines):
                if line.strip() and self._is_security_related(line):
                    threat_level = self._assess_threat_level(line)

                    # Extract specific threat information
                    threat_info = {
                        "chunk_id": chunk_info.chunk_id,
                        "line_content": line.strip(),
                        "threat_level": threat_level,
                        "timestamp": self._extract_timestamp(line),
                        "threat_category": self._categorize_threat(line),
                    }

                    threats.append(threat_info)
                    threat_patterns[threat_level].append(threat_info)

        return {
            "total_threats_detected": len(threats),
            "threats_by_severity": {
                level: len(threats) for level, threats in threat_patterns.items()
            },
            "critical_threats": threat_patterns.get("critical", []),
            "high_priority_threats": threat_patterns.get("high", []),
            "threat_timeline": sorted(
                threats, key=lambda x: x.get("timestamp") or datetime.min
            ),
        }

    def _calculate_security_metrics(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> dict[str, Any]:
        """Calculate security-related metrics."""
        total_lines = sum(len(chunk_text.split("\n")) for chunk_text, _ in chunks)
        security_lines = 0
        failed_auth_count = 0
        intrusion_attempts = 0
        malware_detections = 0

        for chunk_text, chunk_info in chunks:
            for line in chunk_text.split("\n"):
                if line.strip():
                    if self._is_security_related(line):
                        security_lines += 1

                        # Count specific security events
                        line.lower()
                        if any(
                            re.search(pattern, line)
                            for pattern in self.security_patterns[
                                "authentication_failure"
                            ]
                        ):
                            failed_auth_count += 1
                        if any(
                            re.search(pattern, line)
                            for pattern in self.security_patterns["network_intrusion"]
                        ):
                            intrusion_attempts += 1
                        if any(
                            re.search(pattern, line)
                            for pattern in self.security_patterns["malware_detection"]
                        ):
                            malware_detections += 1

        return {
            "security_event_density": (security_lines / total_lines * 100)
            if total_lines > 0
            else 0,
            "failed_authentication_events": failed_auth_count,
            "intrusion_attempt_count": intrusion_attempts,
            "malware_detection_count": malware_detections,
            "security_events_per_chunk": security_lines / len(chunks) if chunks else 0,
        }

    def _detect_security_anomalies(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> dict[str, Any]:
        """Detect security anomalies and unusual patterns."""
        anomalies = []

        # Detect authentication failure spikes
        auth_failures_per_chunk = []
        for chunk_text, chunk_info in chunks:
            failures = sum(
                1
                for line in chunk_text.split("\n")
                if any(
                    re.search(pattern, line)
                    for pattern in self.security_patterns["authentication_failure"]
                )
            )
            auth_failures_per_chunk.append(failures)

        if auth_failures_per_chunk:
            avg_failures = sum(auth_failures_per_chunk) / len(auth_failures_per_chunk)
            for i, failures in enumerate(auth_failures_per_chunk):
                if failures > avg_failures * 3:  # 3x above average
                    anomalies.append(
                        {
                            "type": "authentication_failure_spike",
                            "chunk_id": i,
                            "failure_count": failures,
                            "severity": "high"
                            if failures > avg_failures * 5
                            else "medium",
                        }
                    )

        # Detect unusual security event clustering
        security_events_per_chunk = []
        for chunk_text, chunk_info in chunks:
            events = sum(
                1 for line in chunk_text.split("\n") if self._is_security_related(line)
            )
            security_events_per_chunk.append(events)

        if security_events_per_chunk:
            avg_events = sum(security_events_per_chunk) / len(security_events_per_chunk)
            for i, events in enumerate(security_events_per_chunk):
                if events > avg_events * 4:  # 4x above average
                    anomalies.append(
                        {
                            "type": "security_event_clustering",
                            "chunk_id": i,
                            "event_count": events,
                            "severity": "high",
                        }
                    )

        return {
            "anomalies_detected": len(anomalies),
            "anomaly_details": anomalies,
            "anomaly_types": list(set(anomaly["type"] for anomaly in anomalies)),
        }

    def _generate_security_recommendations(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> list[dict[str, str]]:
        """Generate security recommendations based on analysis."""
        recommendations = []

        # Analyze patterns to generate recommendations
        threat_counts = Counter()
        for chunk_text, _ in chunks:
            for line in chunk_text.split("\n"):
                if self._is_security_related(line):
                    threat_level = self._assess_threat_level(line)
                    threat_counts[threat_level] += 1

        # Generate recommendations based on findings
        if threat_counts["critical"] > 0:
            recommendations.append(
                {
                    "priority": "critical",
                    "category": "immediate_action",
                    "recommendation": f"Immediate investigation required: {threat_counts['critical']} critical security events detected",
                    "action_items": [
                        "Review all critical security events immediately",
                        "Check for signs of system compromise",
                        "Implement emergency response procedures",
                    ],
                }
            )

        if threat_counts["high"] > 10:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "security_monitoring",
                    "recommendation": f"Enhanced monitoring recommended: {threat_counts['high']} high-severity events detected",
                    "action_items": [
                        "Increase security monitoring frequency",
                        "Review and update security policies",
                        "Consider additional security controls",
                    ],
                }
            )

        if threat_counts["medium"] > 50:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "preventive_measures",
                    "recommendation": f"Preventive measures needed: {threat_counts['medium']} medium-severity events detected",
                    "action_items": [
                        "Review authentication mechanisms",
                        "Update security awareness training",
                        "Audit access controls",
                    ],
                }
            )

        return recommendations

    def _analyze_security_timeline(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> dict[str, Any]:
        """Analyze security events over time."""
        timeline_events = []

        for chunk_text, chunk_info in chunks:
            for line in chunk_text.split("\n"):
                if line.strip() and self._is_security_related(line):
                    timestamp = self._extract_timestamp(line)
                    if timestamp:
                        timeline_events.append(
                            {
                                "timestamp": timestamp,
                                "threat_level": self._assess_threat_level(line),
                                "event_type": self._categorize_threat(line),
                                "chunk_id": chunk_info.chunk_id,
                            }
                        )

        # Sort by timestamp
        timeline_events.sort(key=lambda x: x["timestamp"])

        return {
            "total_timeline_events": len(timeline_events),
            "timeline_events": timeline_events,
            "event_frequency_analysis": self._analyze_event_frequency(timeline_events),
        }

    def _identify_attack_patterns(
        self, chunks: list[tuple[str, ChunkInfo]]
    ) -> dict[str, Any]:
        """Identify potential attack patterns and sequences."""
        attack_sequences = []
        current_sequence = []

        for chunk_text, chunk_info in chunks:
            chunk_threats = []
            for line in chunk_text.split("\n"):
                if line.strip() and self._is_security_related(line):
                    threat_category = self._categorize_threat(line)
                    threat_level = self._assess_threat_level(line)
                    chunk_threats.append(
                        {
                            "category": threat_category,
                            "level": threat_level,
                            "chunk_id": chunk_info.chunk_id,
                        }
                    )

            if chunk_threats:
                if (
                    current_sequence
                    and chunk_info.chunk_id - current_sequence[-1]["chunk_id"] > 5
                ):
                    # Gap in sequence, start new one
                    if len(current_sequence) > 1:
                        attack_sequences.append(current_sequence)
                    current_sequence = chunk_threats
                else:
                    current_sequence.extend(chunk_threats)

        # Add final sequence if it exists
        if len(current_sequence) > 1:
            attack_sequences.append(current_sequence)

        return {
            "potential_attack_sequences": len(attack_sequences),
            "attack_sequence_details": attack_sequences[:5],  # Top 5 sequences
            "common_attack_patterns": self._analyze_common_patterns(attack_sequences),
        }

    def _extract_timestamp(self, line: str) -> datetime:
        """Extract timestamp from log line."""
        # Simple timestamp extraction - can be enhanced
        timestamp_patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            r"\w{3} \d{2} \d{2}:\d{2}:\d{2}",
        ]

        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    return datetime.fromisoformat(match.group().replace(" ", "T"))
                except ValueError:
                    continue

        return datetime.now()  # Fallback to current time

    def _categorize_threat(self, line: str) -> str:
        """Categorize the type of security threat."""
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line):
                    return category
        return "unknown"

    def _calculate_overall_risk(self, threat_levels: Counter) -> str:
        """Calculate overall risk level based on threat distribution."""
        if threat_levels["critical"] > 0:
            return "critical"
        elif threat_levels["high"] > 5:
            return "high"
        elif threat_levels["medium"] > 20:
            return "medium"
        else:
            return "low"

    def _analyze_event_frequency(self, timeline_events: list[dict]) -> dict[str, Any]:
        """Analyze frequency patterns in security events."""
        if not timeline_events:
            return {}

        # Group events by hour
        hourly_counts = defaultdict(int)
        for event in timeline_events:
            hour = event["timestamp"].hour
            hourly_counts[hour] += 1

        return {
            "peak_activity_hour": max(hourly_counts, key=hourly_counts.get)
            if hourly_counts
            else None,
            "hourly_distribution": dict(hourly_counts),
            "average_events_per_hour": sum(hourly_counts.values()) / len(hourly_counts)
            if hourly_counts
            else 0,
        }

    def _analyze_common_patterns(
        self, attack_sequences: list[list[dict]]
    ) -> dict[str, int]:
        """Analyze common attack patterns."""
        pattern_counts = Counter()

        for sequence in attack_sequences:
            # Create pattern signature
            pattern = " -> ".join([event["category"] for event in sequence])
            pattern_counts[pattern] += 1

        return dict(pattern_counts.most_common(5))

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        # No special cleanup needed for this plugin
        pass
