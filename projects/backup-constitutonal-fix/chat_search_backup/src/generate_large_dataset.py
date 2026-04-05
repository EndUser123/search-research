#!/usr/bin/env python3
"""Generate large dataset for performance testing SQLite chat search."""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_db import ChatHistoryDB


def generate_large_dataset(num_sessions=1000, avg_messages_per_session=15):
    """Generate large dataset for performance testing.

    Args:
        num_sessions: Number of chat sessions to generate
        avg_messages_per_session: Average number of messages per session
    """
    print("🏗️  Generating Large Dataset for Performance Testing")
    print(f"   Sessions: {num_sessions:,}")
    print(f"   Avg Messages/Session: {avg_messages_per_session}")
    print(f"   Estimated Total Messages: {num_sessions * avg_messages_per_session:,}")

    db = ChatHistoryDB()

    # Topic categories for realistic conversations
    topic_categories = {
        'technical': [
            'GPU optimization', 'database performance', 'API design', 'machine learning',
            'container orchestration', 'security implementation', 'cache strategies',
            'memory management', 'network optimization', 'algorithm design'
        ],
        'project_management': [
            'sprint planning', 'code review', 'deployment strategy', 'team coordination',
            'requirements analysis', 'testing strategy', 'documentation',
            'milestone tracking', 'risk assessment', 'resource allocation'
        ],
        'development': [
            'bug fixes', 'feature implementation', 'refactoring', 'code optimization',
            'unit testing', 'integration testing', 'CI/CD pipeline', 'version control',
            'debugging sessions', 'performance profiling'
        ],
        'architecture': [
            'microservices design', 'system scalability', 'database architecture',
            'API gateway', 'load balancing', 'data replication', 'security architecture',
            'monitoring systems', 'event streaming', 'distributed systems'
        ]
    }

    # Message templates for realistic content
    message_templates = {
        'questions': [
            "How should we implement {topic}?",
            "What's the best approach for {topic}?",
            "Can you help me with {topic}?",
            "I'm having issues with {topic}. Any suggestions?",
            "What are your thoughts on {topic}?",
            "How do we handle {topic} in production?",
            "What's the performance impact of {topic}?",
            "Can we optimize {topic} further?",
            "What are the security considerations for {topic}?",
            "How does {topic} scale with increased load?"
        ],
        'answers': [
            "For {topic}, I recommend implementing a {strategy} approach with {detail}.",
            "The best way to handle {topic} is to use {technology} with {optimization}.",
            "I've implemented {topic} using {method} which achieved {result}.",
            "Based on my experience, {topic} works best when you apply {technique}.",
            "The {topic} challenge can be solved by implementing {solution} and monitoring {metric}.",
            "I suggest using {framework} for {topic} with {configuration} settings.",
            "The {topic} implementation should focus on {priority} and include {feature}.",
            "For optimal {topic} performance, consider using {tool} and {approach}.",
            "The {topic} architecture should be designed with {principle} in mind.",
            "I've successfully implemented {topic} in previous projects using {methodology}."
        ],
        'followups': [
            "That's a great point. Have you considered {alternative}?",
            "I agree. Let me implement {implementation} right now.",
            "Excellent suggestion. I'll add {feature} to the solution.",
            "Good thinking. We should also test {test_case} to ensure robustness.",
            "Perfect. I'll create a {artifact} to demonstrate this approach.",
            "I like that idea. Let me create {deliverable} with {specification}.",
            "Great insight. I'll implement {enhancement} to improve {performance}.",
            "Thanks for the feedback. I'll update {component} with {improvement}.",
            "Valid concern. Let me add {safeguard} to handle {edge_case}.",
            "Absolutely. I'll create {resource} to document {process}."
        ]
    }

    # Technical terms and technologies
    technical_terms = [
        'Kubernetes', 'Docker', 'Redis', 'PostgreSQL', 'MongoDB', 'Elasticsearch',
        'React', 'Vue.js', 'Angular', 'Node.js', 'Python', 'Java', 'Go', 'Rust',
        'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'Apache Spark',
        'AWS', 'Azure', 'GCP', 'Terraform', 'Ansible', 'Jenkins', 'GitLab CI',
        'RESTful API', 'GraphQL', 'gRPC', 'WebSockets', 'HTTP/2', 'TLS/SSL',
        'Microservices', 'Serverless', 'Event-driven', 'CQRS', 'Event Sourcing',
        'Machine Learning', 'Deep Learning', 'Neural Networks', 'NLP', 'Computer Vision'
    ]

    strategies = [
        'layered architecture', 'microservices pattern', 'event-driven design',
        'domain-driven design', 'clean architecture', 'hexagonal architecture',
        'reactive programming', 'functional programming', 'object-oriented design'
    ]

    technologies = [
        'Apache Kafka', 'RabbitMQ', 'Apache Cassandra', 'CockroachDB', 'TimescaleDB',
        'Prometheus', 'Grafana', 'ELK Stack', 'Jaeger', 'Zipkin', 'Istio',
        'Kong API Gateway', 'NGINX', 'HAProxy', 'Envoy Proxy', 'Consul'
    ]

    generated_sessions = 0
    total_messages = 0

    print("\n🔄 Generating sessions...")

    for session_num in range(num_sessions):
        # Random session parameters
        num_messages = random.randint(
            max(5, avg_messages_per_session - 5),
            avg_messages_per_session + 10
        )

        # Choose topic category and specific topic
        category = random.choice(list(topic_categories.keys()))
        topic = random.choice(topic_categories[category])

        # Generate session metadata
        session_start = datetime.now() - timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        session_id = f"perf_test_{session_num:06d}"
        session_data = {
            "session_id": session_id,
            "model": random.choice([
                "claude-sonnet-4-5-20250929",
                "claude-opus-4-5-20251101",
                "claude-haiku-3-5-20241022"
            ]),
            "metadata": {
                "topic": topic,
                "category": category,
                "generated_for": "performance_testing",
                "original_format": "synthetic_large_dataset"
            },
            "messages": []
        }

        # Generate conversation
        messages = []
        current_time = session_start

        for msg_num in range(num_messages):
            # Determine message type and content
            if msg_num == 0 or (msg_num > 0 and random.random() < 0.4):
                # Question from user
                template = random.choice(message_templates['questions'])
                role = "user"
            else:
                # Answer or follow-up from assistant
                if msg_num == 1 or random.random() < 0.7:
                    template = random.choice(message_templates['answers'])
                else:
                    template = random.choice(message_templates['followups'])
                role = "assistant"

            # Fill template with realistic content
            content = template.format(
                topic=topic,
                strategy=random.choice(strategies),
                technology=random.choice(technologies),
                method=random.choice(['agile', 'waterfall', 'scrum', 'kanban']),
                tool=random.choice(technical_terms),
                approach=random.choice(['proactive', 'reactive', 'hybrid', 'incremental']),
                detail=f"{random.choice(['performance', 'security', 'scalability', 'maintainability'])} optimization",
                optimization=random.choice(['caching', 'indexing', 'compression', 'batching']),
                configuration=random.choice(['default', 'custom', 'production', 'development']),
                result=random.choice(['99.9% uptime', '50% faster performance', '90% cost reduction', '10x scalability']),
                technique=random.choice(['circuit breaker', 'rate limiting', 'retry logic', 'bulkheads']),
                solution=random.choice(['distributed cache', 'message queue', 'load balancer', 'API gateway']),
                metric=random.choice(['response time', 'throughput', 'error rate', 'resource utilization']),
                framework=random.choice(['Spring Boot', 'Django', 'Flask', 'Express.js', 'FastAPI']),
                priority=random.choice(['high availability', 'low latency', 'high throughput', 'data consistency']),
                feature=random.choice(['monitoring', 'logging', 'tracing', 'alerting']),
                principle=random.choice(['single responsibility', 'open/closed', 'dependency inversion', 'interface segregation']),
                enhancement=random.choice(['performance monitoring', 'security scanning', 'automated testing', 'documentation']),
                improvement=random.choice(['code optimization', 'database indexing', 'caching layer', 'connection pooling']),
                performance=random.choice(['overall system performance', 'query response times', 'throughput', 'resource efficiency']),
                safeguard=random.choice(['input validation', 'output sanitization', 'rate limiting', 'authentication']),
                edge_case=random.choice(['network failures', 'data corruption', 'high load', 'concurrent access']),
                deliverable=random.choice(['prototype', 'specification', 'documentation', 'test suite']),
                specification=random.choice(['API spec', 'database schema', 'deployment guide', 'user manual']),
                alternative=random.choice(['microservices', 'serverless', 'monolithic', 'hybrid approach']),
                implementation=random.choice(['proof of concept', 'production ready', 'minimum viable product', 'enterprise solution']),
                test_case=random.choice(['load testing', 'security testing', 'integration testing', 'end-to-end testing']),
                artifact=random.choice(['diagram', 'prototype', 'documentation', 'configuration']),
                component=random.choice(['service', 'module', 'library', 'utility']),
                methodology=random.choice(['Agile', 'Scrum', 'Kanban', 'DevOps', 'CI/CD']),
                resource=random.choice(['wiki page', 'code repository', 'deployment script', 'monitoring dashboard']),
                process=random.choice(['development workflow', 'deployment pipeline', 'testing strategy', 'incident response'])
            )

            # Add technical terms for realism
            if random.random() < 0.3:
                content += f" Using {random.choice(technical_terms)} for better {random.choice(['performance', 'reliability', 'scalability'])}."

            if random.random() < 0.2:
                content += f" The solution should handle {random.randint(100, 10000)} requests per second."

            # Create message
            message = {
                "role": role,
                "content": content,
                "timestamp": current_time.isoformat() + "Z",
                "token_count": len(content.split()) + random.randint(5, 15),
                "metadata": {
                    "type": "synthetic",
                    "session_position": msg_num,
                    "topic": topic,
                    "category": category
                }
            }

            messages.append(message)

            # Advance time for next message
            current_time += timedelta(
                seconds=random.randint(30, 300),  # 30 seconds to 5 minutes between messages
                minutes=random.randint(0, 10)     # Additional 0-10 minutes
            )

        session_data["messages"] = messages

        # Store session in database
        stored_session_id = db.store_session(session_data)
        generated_sessions += 1
        total_messages += len(messages)

        # Progress reporting
        if generated_sessions % 100 == 0:
            print(f"   Generated {generated_sessions:,} sessions, {total_messages:,} messages")

    print("\n✅ Dataset Generation Complete!")
    print(f"   Sessions Generated: {generated_sessions:,}")
    print(f"   Total Messages: {total_messages:,}")
    print(f"   Avg Messages/Session: {total_messages / generated_sessions:.1f}")

    # Show database statistics
    print("\n📊 Final Database Statistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        elif isinstance(value, int):
            print(f"   {key}: {value:,}")
        else:
            print(f"   {key}: {value}")

    return generated_sessions, total_messages


if __name__ == "__main__":
    # Generate a substantial dataset for performance testing
    generate_large_dataset(
        num_sessions=500,      # 500 sessions
        avg_messages_per_session=20  # ~10,000 total messages
    )
