---
source_id: "e66b9455-6fde-4c59-9a1c-cdedbf0ba29b"
title: "How to Implement the Circuit Breaker Pattern in Microservices - OneUptime"
notebook_id: 84f90a47-9448-4652-82e1-c8dec495fc68
url: https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view
type: web_page
exported: 2026-07-27
---

# How to Implement the Circuit Breaker Pattern in Microservices - OneUptime
How to Implement the Circuit Breaker Pattern in Microservices

Skip to main content

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#main-content

OneUptime

https://oneuptime.com/

Open menu

Products

Essentials

Monitoring Uptime & synthetic checks

https://oneuptime.com/product/monitoring

Status Page Communicate incidents to users

https://oneuptime.com/product/status-page

Incidents Detect, manage & resolve

https://oneuptime.com/product/incident-management

On-Call & Alerts Smart routing & escalations

https://oneuptime.com/product/on-call

Scheduled Maintenance Plan & communicate downtime

https://oneuptime.com/product/scheduled-maintenance

Observability

Logs Fastest log ingest & search

https://oneuptime.com/product/logs-management

Metrics Application & infra metrics

https://oneuptime.com/product/metrics

Traces Distributed request tracing

https://oneuptime.com/product/traces

Exceptions Error tracking & debugging

https://oneuptime.com/product/exceptions

Kubernetes Cluster & pod observability

https://oneuptime.com/product/kubernetes

Profiles CPU & memory profiling

https://oneuptime.com/product/profiles

Automation & Analytics

Workflows No-code automation builder

https://oneuptime.com/product/workflows

Dashboards Custom data visualizations

https://oneuptime.com/product/dashboards

AI Agent Auto-fix issues with AI-powered PRs. Let AI analyze incidents and automatically create pull requests to resolve them.

https://oneuptime.com/product/ai-agent

Resources

Documentation

https://oneuptime.com/docs

 

API Reference

https://oneuptime.com/reference

 

GitHub

https://github.com/oneuptime/oneuptime

 

Blog & Guides

https://oneuptime.com/blog

Get Started

Start Free Trial

https://oneuptime.com/accounts/register

 

Request Demo

https://oneuptime.com/enterprise/demo

sales@oneuptime.com

mailto:sales@oneuptime.com

Open Source — Self-host or use our cloud. Your data, your choice.

View Pricing

https://oneuptime.com/pricing

 

Enterprise

https://oneuptime.com/enterprise/overview

Enterprise

Enterprise

Built for how you work

Scale your reliability operations with enterprise-grade tools.

Enterprise Overview Scale with confidence

https://oneuptime.com/enterprise/overview

Request Demo See it in action

https://oneuptime.com/enterprise/demo

Contact Sales

https://oneuptime.com/legal/contact

Enterprise

Enterprise Overview Solutions for large organizations

https://oneuptime.com/enterprise/overview

Request Demo Schedule a personalized demo

https://oneuptime.com/enterprise/demo

Teams

DevOps

https://oneuptime.com/solutions/devops

SRE

https://oneuptime.com/solutions/sre

Platform

https://oneuptime.com/solutions/platform

Developers

https://oneuptime.com/solutions/developers

Industries

FinTech

https://oneuptime.com/industries/fintech

SaaS

https://oneuptime.com/industries/saas

Healthcare

https://oneuptime.com/industries/healthcare

E-Commerce

https://oneuptime.com/industries/ecommerce

Media

https://oneuptime.com/industries/media

Government

https://oneuptime.com/industries/government

Documentation

https://oneuptime.com/docs

 

Pricing

https://oneuptime.com/pricing

 

Blog

https://oneuptime.com/blog

Get Started Free

https://oneuptime.com/accounts/register

Pricing

https://oneuptime.com/pricing

Resources

Resources

Learn & Connect

Everything you need to get started and succeed.

Documentation Guides & tutorials

https://oneuptime.com/docs

API Reference REST API & SDKs

https://oneuptime.com/reference

Star on GitHub

https://github.com/oneuptime/oneuptime

Learn

Blog News & insights

https://oneuptime.com/blog

Status System status

https://status.oneuptime.com/

Changelog What's new

https://github.com/OneUptime/oneuptime/releases

Videos Watch & learn

https://www.youtube.com/@OneUptimehq

Support

Help Center

https://oneuptime.com/support

Contact Us

mailto:support@oneuptime.com

Company

About Us

https://oneuptime.com/about

Merch Store

https://shop.oneuptime.com/

Legal

https://oneuptime.com/legal

 

Privacy

https://oneuptime.com/legal/privacy

 

Terms

https://oneuptime.com/legal/terms

100% Open Source

Sign in

https://oneuptime.com/accounts

 

Sign up

https://oneuptime.com/accounts/register

 

Close menu

Status Page

https://oneuptime.com/product/status-page

Incidents

https://oneuptime.com/product/incident-management

Monitoring

https://oneuptime.com/product/monitoring

On-Call

https://oneuptime.com/product/on-call

Maintenance

https://oneuptime.com/product/scheduled-maintenance

Logs

https://oneuptime.com/product/logs-management

Metrics

https://oneuptime.com/product/metrics

Traces

https://oneuptime.com/product/traces

Exceptions

https://oneuptime.com/product/exceptions

Kubernetes

https://oneuptime.com/product/kubernetes

Profiles

https://oneuptime.com/product/profiles

Workflows

https://oneuptime.com/product/workflows

Dashboards

https://oneuptime.com/product/dashboards

AI Agent

https://oneuptime.com/product/ai-agent

Enterprise

DevOps

https://oneuptime.com/solutions/devops

SRE

https://oneuptime.com/solutions/sre

Platform

https://oneuptime.com/solutions/platform

Pricing

https://oneuptime.com/pricing

 

Docs

https://oneuptime.com/docs

 

Request Demo

https://oneuptime.com/enterprise/demo

 

Support

https://oneuptime.com/support

Sign up

https://oneuptime.com/accounts/register

Existing customer? 

Sign in

https://oneuptime.com/accounts

 

How to Implement the Circuit Breaker Pattern in Microservices

Learn how to implement the circuit breaker pattern in microservices for graceful degradation and fault tolerance.

 @nawazdhandala

https://github.com/nawazdhandala

• Feb 20, 2026

• Reading time 6 min read

Microservice

https://oneuptime.com/blog/tag/microservice

 

Circuit Breaker

https://oneuptime.com/blog/tag/circuit-breaker

 

Resilience

https://oneuptime.com/blog/tag/resilience

 

Fault Tolerance

https://oneuptime.com/blog/tag/fault-tolerance

 

Pattern

https://oneuptime.com/blog/tag/pattern

On this page

The Problem: Cascading Failures

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#the-problem-cascading-failures

 

How the Circuit Breaker Works

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#how-the-circuit-breaker-works

 

Implementing a Circuit Breaker in Python

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#implementing-a-circuit-breaker-in-python

 

Using the Circuit Breaker

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#using-the-circuit-breaker

 

Circuit Breaker State Flow

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#circuit-breaker-state-flow

 

Circuit Breaker with Fallbacks

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#circuit-breaker-with-fallbacks

 

Monitoring Circuit Breakers

https://oneuptime.com/blog/post/2026-02-20-microservices-circuit-breaker/view#monitoring-circuit-breakers

 

https://twitter.com/intent/tweet?text=%20How%20to%20Implement%20the%20Circuit%20Breaker%20Pattern%20in%20Microservices&url=https%3A%2F%2Foneuptime.com%2Fblog%2Fpost%2F2026-02-20-microservices-circuit-breaker%2Fview

 

https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Foneuptime.com%2Fblog%2Fpost%2F2026-02-20-microservices-circuit-breaker%2Fview

 

https://news.ycombinator.com/submitlink?u=https%3A%2F%2Foneuptime.com%2Fblog%2Fpost%2F2026-02-20-microservices-circuit-breaker%2Fview&t=%20How%20to%20Implement%20the%20Circuit%20Breaker%20Pattern%20in%20Microservices

In a microservices architecture, a single failing service can cascade failures across the entire system. The circuit breaker pattern prevents this by detecting failures and stopping requests to unhealthy services, giving them time to recover. This guide shows you how to implement circuit breakers from scratch and with popular libraries.

The Problem: Cascading Failures

When Service A calls Service B and Service B is down, Service A keeps retrying. This ties up threads, exhausts connection pools, and eventually causes Service A to fail too.

Service B (Down) Service A User Service B (Down) Service A User Service is down Thread pool exhausted Service A now fails too Request Call (timeout 30s) Connection timeout Retry 1 (timeout 30s) Connection timeout Retry 2 (timeout 30s) Connection timeout 503 after 90 seconds

How the Circuit Breaker Works

The circuit breaker has three states: Closed (normal), Open (blocking), and Half-Open (testing).

Failure threshold exceeded

Timeout expires

Test request succeeds

Test request fails

Closed

Requests pass through

Track success/failure counts

Open

All requests rejected immediately

Return fallback or error

HalfOpen

Allow limited test requests

Evaluate if service recovered

Implementing a Circuit Breaker in Python

PythonCopy# circuit_breaker.py

# A complete circuit breaker implementation.
# Tracks failures and opens the circuit when a threshold is exceeded.

import time
import threading
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field


class CircuitState(Enum):
    """The three states of a circuit breaker."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Blocking all requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for the circuit breaker."""
    # Number of failures before opening the circuit
    failure_threshold: int = 5
    # How long to wait before testing (seconds)
    recovery_timeout: int = 30
    # Number of test requests allowed in half-open state
    half_open_max_calls: int = 3
    # Sliding window size for tracking failures (seconds)
    window_size: int = 60


class CircuitBreaker:
    """
    Circuit breaker that wraps calls to external services.
    Opens the circuit when failures exceed the threshold,
    preventing cascading failures.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Get the current state, checking for recovery timeout."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    # Transition to half-open to test recovery
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    print(f"[{self.name}] Circuit half-open, testing recovery")
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        Raises CircuitOpenError if the circuit is open.
        """
        current_state = self.state

        # If circuit is open, fail fast without calling the service
        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is open. "
                f"Retry after {self.config.recovery_timeout}s"
            )

        # If half-open, check if we exceeded the test call limit
        if current_state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' half-open call limit reached"
                    )
                self._half_open_calls += 1

        # Attempt the call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                # If enough test calls succeed, close the circuit
                if self._success_count >= self.config.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    print(f"[{self.name}] Circuit closed, service recovered")
            else:
                # Reset failure count on success in closed state
                self._failure_count = 0

    def _on_failure(self):
        """Handle a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state reopens the circuit
                self._state = CircuitState.OPEN
                print(f"[{self.name}] Circuit reopened, service still failing")
            elif self._failure_count >= self.config.failure_threshold:
                # Threshold exceeded, open the circuit
                self._state = CircuitState.OPEN
                print(f"[{self.name}] Circuit opened after "
                      f"{self._failure_count} failures")


class CircuitOpenError(Exception):
    """Raised when a call is attempted on an open circuit."""
    pass


Show all 129 lines

Using the Circuit Breaker

PythonCopy# usage.py
# Wrap external service calls with the circuit breaker.
# When the payment service fails, the circuit opens
# and returns a fallback response instead of hanging.

import requests
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitOpenError

# Create a circuit breaker for the payment service
payment_breaker = CircuitBreaker(
    name="payment-service",
    config=CircuitBreakerConfig(
        failure_threshold=3,    # Open after 3 failures
        recovery_timeout=15,    # Wait 15 seconds before testing
        half_open_max_calls=2,  # Allow 2 test requests
    )
)


def call_payment_service(order_id: str, amount: float) -> dict:
    """
    Call the payment service with circuit breaker protection.
    Falls back to a queued payment if the circuit is open.
    """
    def make_request():
        response = requests.post(
            "http://payment-service:8080/charge",
            json={"order_id": order_id, "amount": amount},
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    try:
        # Route the call through the circuit breaker
        return payment_breaker.call(make_request)
    except CircuitOpenError:
        # Fallback: queue the payment for later processing
        print(f"Payment service unavailable, queuing payment for {order_id}")
        return {
            "status": "queued",
            "order_id": order_id,
            "message": "Payment will be processed when the service recovers"
        }
    except requests.exceptions.RequestException as e:
        # The call went through the breaker but failed
        # The breaker has already recorded the failure
        print(f"Payment request failed: {e}")
        return {"status": "failed", "error": str(e)}


Circuit Breaker State Flow

Closed

Yes

No

No

Yes

Open

No

Yes

Half-Open

Yes

Yes

No

No

Request Arrives

Circuit State?

Forward to Service

Success?

Return Response

Reset failure count

Increment failure count

Threshold exceeded?

Return Error

Open Circuit

Recovery timeout elapsed?

Return Fallback Immediately

Transition to Half-Open

Forward Test Request

Success?

Enough successes?

Close Circuit

Allow More Tests

Reopen Circuit

Circuit Breaker with Fallbacks

Different fallback strategies suit different scenarios.

PythonCopy# fallbacks.py
# Common fallback strategies for circuit breaker patterns.


def cached_fallback(cache: dict, key: str) -> dict:
    """
    Return cached data when the primary service is unavailable.
    Useful for read-heavy services where stale data is acceptable.
    """
    if key in cache:
        return {"data": cache[key], "source": "cache", "stale": True}
    return {"data": None, "source": "cache", "error": "No cached data"}


def default_fallback() -> dict:
    """
    Return a sensible default when no cached data is available.
    Useful for non-critical features like recommendations.
    """
    return {
        "recommendations": [],
        "source": "default",
        "message": "Recommendations temporarily unavailable"
    }


def queue_fallback(queue_client, task: dict) -> dict:
    """
    Queue the operation for later retry when the service recovers.
    Useful for write operations that must eventually complete.
    """
    queue_client.enqueue("deferred_tasks", task)
    return {
        "status": "queued",
        "message": "Your request has been queued and will be processed shortly"
    }


Monitoring Circuit Breakers

Track circuit breaker state changes, trip frequency, and fallback usage to understand service health.

State Changes

Trip Events

Fallback Usage

Circuit Breaker

Metrics

Alerts

Dashboard

Grafana

PagerDuty / OneUptime

OneUptime ( 

https://oneuptime.com

https://oneuptime.com/

) monitors your services and detects the conditions that trigger circuit breakers. By setting up endpoint monitors and alerting rules, OneUptime can notify your team when a downstream service starts failing - often before the circuit breaker even trips. Combine circuit breaker metrics with OneUptime's status pages to give stakeholders real-time visibility into service health and degraded functionality.

Share this article 

https://twitter.com/intent/tweet?text=%20How%20to%20Implement%20the%20Circuit%20Breaker%20Pattern%20in%20Microservices&url=https%3A%2F%2Foneuptime.com%2Fblog%2Fpost%2F2026-02-20-microservices-circuit-breaker%2Fview

 

https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Foneuptime.com%2Fblog%2Fpost%2F2026-02-20-microservices-circuit-breaker%2Fview

 

https://news.ycombinator.com/submitlink?u=https%3A%2F%2Foneuptime.com%2Fblog%2Fpost%2F2026-02-20-microservices-circuit-breaker%2Fview&t=%20How%20to%20Implement%20the%20Circuit%20Breaker%20Pattern%20in%20Microservices

 

Nawaz Dhandala

Author

@nawazdhandala • Feb 20, 2026 • 6 min read

Nawaz is building OneUptime with a passion for engineering reliable systems and improving observability.

GitHub

https://github.com/nawazdhandala

Improve this Blog Post

All our blog posts are open source. Found a typo, want to add more detail, or have a better explanation? Anyone can contribute and make this post better for everyone.

Edit this Post on GitHub

https://github.com/oneuptime/blog/tree/master/posts/2026-02-20-microservices-circuit-breaker

 

Contributing Guidelines

https://github.com/oneuptime/blog

Open source

https://github.com/oneuptime/oneuptime

OneUptime is the Open-Source Observability Platform

Your complete reliability stack unified: infrastructure monitoring, incident management, status pages, and APM. Open-source and self-hostable.

Get started for free

https://oneuptime.com/accounts/register

 

Request a demo

https://oneuptime.com/enterprise/demo

Status Page Real-time status updates

https://oneuptime.com/product/status-page

Incidents Detect and resolve fast

https://oneuptime.com/product/incident-management

Monitoring Monitor any resource

https://oneuptime.com/product/monitoring

On-Call Smart alert routing

https://oneuptime.com/product/on-call

Maintenance Plan & communicate downtime

https://oneuptime.com/product/scheduled-maintenance

Logs Fastest log ingest and search

https://oneuptime.com/product/logs-management

Metrics Performance insights

https://oneuptime.com/product/metrics

Traces End-to-end distributed tracing

https://oneuptime.com/product/traces

Exceptions Catch and fix bugs early

https://oneuptime.com/product/exceptions

Workflows Automate any process

https://oneuptime.com/product/workflows

Dashboards Visualize all your data

https://oneuptime.com/product/dashboards

Kubernetes Monitor K8s clusters

https://oneuptime.com/product/kubernetes

Profiles CPU & memory profiling

https://oneuptime.com/product/profiles

AI Agent Automatically detect, diagnose, and resolve incidents with AI-powered root cause analysis and code fixes.

https://oneuptime.com/product/ai-agent

We use cookies to enhance your browsing experience and provide personalized content. By clicking "Accept," you consent to the use of cookies.

Our product uses both first-party and third-party cookies for session storage and for various other purposes.

Please note that disabling certain cookies may affect the functionality and performance of our product.

For more information about how we handle your data and cookies, please read our Privacy Policy.

By continuing to use our site without changing your cookie settings, you agree to our use of cookies as described above. See our 

terms

https://oneuptime.com/legal/terms

 and our 

privacy policy

https://oneuptime.com/legal/privacy

Accept all Reject all

Footer

Open Source Observability

Build reliable systems with confidence

Join thousands of developers using OneUptime to monitor, debug, and optimize their infrastructure, stack, and apps.

Read Blog

https://oneuptime.com/blog

 

Star on GitHub

https://github.com/oneuptime/oneuptime

The complete open-source observability platform. Monitor, debug, and improve your entire stack in one place.

GitHub

https://github.com/oneuptime/oneuptime

 

X

https://x.com/oneuptimehq

 

YouTube

https://www.youtube.com/@OneUptimeHQ

 

Reddit

https://www.reddit.com/r/oneuptimehq/

 

LinkedIn

https://www.linkedin.com/company/oneuptime

Trusted by thousands of teams worldwide - from Fortune 500 enterprises to fast-growing startups.

Products

Status Page

https://oneuptime.com/product/status-page

Incidents

https://oneuptime.com/product/incident-management

Monitoring

https://oneuptime.com/product/monitoring

On-Call

https://oneuptime.com/product/on-call

Logs

https://oneuptime.com/product/logs-management

Metrics

https://oneuptime.com/product/metrics

Traces

https://oneuptime.com/product/traces

Exceptions

https://oneuptime.com/product/exceptions

Profiles

https://oneuptime.com/product/profiles

Kubernetes

https://oneuptime.com/product/kubernetes

Workflows

https://oneuptime.com/product/workflows

Dashboards

https://oneuptime.com/product/dashboards

AI Agent

https://oneuptime.com/product/ai-agent

Solutions

Enterprise

https://oneuptime.com/enterprise/overview

Request Demo

https://oneuptime.com/enterprise/demo

Pricing

https://oneuptime.com/pricing

Data Residency

https://oneuptime.com/legal/data-residency

Teams

DevOps

https://oneuptime.com/solutions/devops

SRE

https://oneuptime.com/solutions/sre

Platform

https://oneuptime.com/solutions/platform

Developers

https://oneuptime.com/solutions/developers

Tools

MCP Server

https://oneuptime.com/tool/mcp-server

CLI

https://oneuptime.com/tool/cli

Resources

Documentation

https://oneuptime.com/docs

API Reference

https://oneuptime.com/reference

Blog

https://oneuptime.com/blog

Help & Support

https://oneuptime.com/support

GitHub

https://github.com/oneuptime/oneuptime

Changelog

https://github.com/oneuptime/oneuptime/releases

Open Source Friends

https://oneuptime.com/oss-friends

Industries

FinTech

https://oneuptime.com/industries/fintech

SaaS

https://oneuptime.com/industries/saas

Healthcare

https://oneuptime.com/industries/healthcare

E-Commerce

https://oneuptime.com/industries/ecommerce

Media

https://oneuptime.com/industries/media

Government

https://oneuptime.com/industries/government

Company

About Us

https://oneuptime.com/about

Careers

https://github.com/OneUptime/interview

Merch Store

https://shop.oneuptime.com/

Contact

https://oneuptime.com/legal/contact

Legal

Terms of Service

https://oneuptime.com/legal/terms

Privacy Policy

https://oneuptime.com/legal/privacy

SLA

https://oneuptime.com/legal/sla

Legal Center

https://oneuptime.com/legal

Compare

vs PagerDuty

https://oneuptime.com/compare/pagerduty

vs Statuspage

https://oneuptime.com/compare/statuspage.io

vs Incident.io

https://oneuptime.com/compare/incident.io

vs Pingdom

https://oneuptime.com/compare/pingdom

vs Datadog

https://oneuptime.com/compare/datadog

vs New Relic

https://oneuptime.com/compare/newrelic

vs Better Stack

https://oneuptime.com/compare/better-uptime

vs Uptime Robot

https://oneuptime.com/compare/uptime-robot

vs Checkly

https://oneuptime.com/compare/checkly

vs SigNoz

https://oneuptime.com/compare/signoz

© 2026 HackerBay, Inc. All rights reserved.

Open Source

https://github.com/oneuptime/oneuptime

 | Made with care for developers worldwide

SOC 2

https://oneuptime.com/legal/soc-2

 

HIPAA

https://oneuptime.com/legal/hipaa

 

GDPR

https://oneuptime.com/legal/gdpr

 

ISO 27001

https://oneuptime.com/legal/iso-27001
