---
title: "OpenTelemetry Logging"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  OpenTelemetry logging encompasses the standards, approaches, and techniques for capturing, structuring, and propagating diagnostic data within the OpenTelemetry observability framework, enabling interoperability across languages and platforms.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 5afa7287-dbfe-4ae2-a716-8fd6de80d224" (Claude Code - Observability & Logging, synced 2026-07-28)
  - "How to configure tracing_subscriber output format (json or plain text) based on env variable? - Stack Overflow" (https://stackoverflow.com/questions/78298535/how-to-configure-tracing-subscriber-output-format-json-or-plain-text-based-on, transcript synced 2026-07-28)
  - "Logs API - OpenTelemetry" (https://opentelemetry.io/docs/specs/otel/logs/api/, transcript synced 2026-07-28)
  - "open-telemetry/opentelemetry-rust - GitHub" (https://github.com/open-telemetry/opentelemetry-rust, transcript synced 2026-07-28)
  - "How OpenTelemetry Logging Works (with Examples) - Dash0" (https://www.dash0.com/knowledge/opentelemetry-logging-explained, transcript synced 2026-07-28)
  - "What is structured metadata | Grafana Loki documentation" (https://grafana.com/docs/loki/latest/get-started/labels/structured-metadata/, transcript synced 2026-07-28)
  - "[FEATURE] Expose tool_use_id (and optionally W3C Baggage) as environment variables in Bash tool shell processes · Issue #35953 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/35953, transcript synced 2026-07-28)
  - "logfmt — brandur.org" (https://brandur.org/logfmt, transcript synced 2026-07-28)
  - "How to Structure Logs Properly in Python with OpenTelemetry - OneUptime" (https://oneuptime.com/blog/post/2025-01-06-python-structured-logging-opentelemetry/view, transcript synced 2026-07-28)
  - "Intercept and control agent behavior with hooks - Claude API Docs" (https://platform.claude.com/docs/en/agent-sdk/hooks, transcript synced 2026-07-28)
  - "Go's slog: Modern Structured Logging Made Easy | by Leapcell - Medium" (https://leapcell.medium.com/gos-slog-modern-structured-logging-made-easy-b8468ac71309, transcript synced 2026-07-28)
  - "Python Logging Module: A Complete Guide - Dash0" (https://www.dash0.com/guides/logging-in-python, transcript synced 2026-07-28)
  - "10 Python Logging Best Practices for Cybersecurity - Apriorit" (https://www.apriorit.com/dev-blog/cybersecurity-logging-python, transcript synced 2026-07-28)
  - "Event-driven architectures with Apache Kafka | Redpanda" (https://www.redpanda.com/guides/kafka-use-cases-event-driven-architecture, transcript synced 2026-07-28)
  - "Observability primer | OpenTelemetry" (https://opentelemetry.io/docs/concepts/observability-primer/, transcript synced 2026-07-28)
  - "Python Logging Explained: Best Practices & Production Tips UptimeRobot Knowledge Hub" (https://uptimerobot.com/knowledge-hub/logging/python-logging-explained/, transcript synced 2026-07-28)
  - "OpenTelemetry Instrumentation - Datadog Docs" (https://docs.datadoghq.com/llm_observability/instrumentation/otel_instrumentation/, transcript synced 2026-07-28)
  - "How to Create Structured JSON Logs with tracing in Rust - OneUptime" (https://oneuptime.com/blog/post/2026-01-25-structured-json-logs-tracing-rust/view, transcript synced 2026-07-28)
  - "AI observability in multi-agent systems using OpenTelemetry - Outshift | Cisco" (https://outshift.cisco.com/blog/ai-ml/ai-observability-multi-agent-systems-opentelemetry, transcript synced 2026-07-28)
  - "NotebookLM source 3461761a-0094-4892-99a8-500fe8954cd1" (Strategic Architecture for Diagnostic Logging and Observability in Python: Paradigms, Performance, and Compliance in 2025, synced 2026-07-28)
  - "OpenTelemetry Logs: Benefits, Concepts, & Best Practices - groundcover" (https://www.groundcover.com/opentelemetry/opentelemetry-logs, transcript synced 2026-07-28)
  - "Context propagation - OpenTelemetry" (https://opentelemetry.io/docs/concepts/context-propagation/, transcript synced 2026-07-28)
  - "python logging performance comparison and options - Stack Overflow" (https://stackoverflow.com/questions/35520160/python-logging-performance-comparison-and-options, transcript synced 2026-07-28)
  - "Event Driven Architecture Done Right: How to Scale Systems with Quality in 2025 - Growin" (https://www.growin.com/blog/event-driven-architecture-scale-systems-2025/, transcript synced 2026-07-28)
  - "Semantic conventions for generative AI metrics | OpenTelemetry" (https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/, transcript synced 2026-07-28)
  - "NotebookLM source 39ad0c90-2cfb-4732-9bde-efbc846d77a1" (Current UPS Logging Implementation, synced 2026-07-28)
  - "Getting Started with Tracing in Rust - Shuttle.dev" (https://www.shuttle.dev/blog/2024/01/09/getting-started-tracing-rust, transcript synced 2026-07-28)
  - "Python Logging Best Practices - Obvious and Not-So-Obvious ..." (https://signoz.io/guides/python-logging-best-practices/, transcript synced 2026-07-28)
  - "Top 10 Log Monitoring Tools in 2025: Complete Guide - OpenObserve" (https://openobserve.ai/blog/top-10-log-monitoring-tools-2025/, transcript synced 2026-07-28)
  - "Redirecting all kinds of stdout in Python - Eli Bendersky's website" (https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/, transcript synced 2026-07-28)
  - "Logging in Go with Slog: A Practitioner's Guide - Dash0" (https://www.dash0.com/guides/logging-in-go-with-slog, transcript synced 2026-07-28)
  - "Spent a bunch of time choosing between Loguru, Structlog and native logging - Reddit" (https://www.reddit.com/r/Python/comments/1p6qy1e/spent_a_bunch_of_time_choosing_between_loguru/, transcript synced 2026-07-28)
  - "Hooks - Claude Code Best Practice - Mintlify" (https://mintlify.com/shanraisshan/claude-code-best-practice/concepts/hooks, transcript synced 2026-07-28)
  - "Sending `tracing` events to MPSC Channel - help - Rust Users Forum" (https://users.rust-lang.org/t/sending-tracing-events-to-mpsc-channel/123550, transcript synced 2026-07-28)
  - "How to Propagate OpenTelemetry Trace Context Through Celery Message Headers" (https://oneuptime.com/blog/post/2026-02-06-propagate-opentelemetry-trace-context-celery-headers/view, transcript synced 2026-07-28)
  - "OpenTelemetry Trace Context Propagation [Python] - Uptrace" (https://uptrace.dev/get/opentelemetry-python/propagation, transcript synced 2026-07-28)
  - "logging.handlers — Logging handlers — Python 3.14.3 documentation" (https://docs.python.org/3/library/logging.handlers.html, transcript synced 2026-07-28)
  - "logging | Python Best Practices – Real Python" (https://realpython.com/ref/best-practices/logging/, transcript synced 2026-07-28)
  - "Ultimate Event-Driven Architecture with Python and Apache Kafka - eBooks2go" (https://www.ebooks2go.com/img/samplefiles/9789349888289_Sample.pdf, transcript synced 2026-07-28)
  - "Production-Grade Logging in Node.js with Pino - Dash0" (https://www.dash0.com/guides/logging-in-node-js-with-pino, transcript synced 2026-07-28)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-07-28)
  - "Label best practices | Grafana Loki documentation - Grafana Labs" (https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/, transcript synced 2026-07-28)
  - "DataDog vs Grafana [2025 comparison] - Uptrace" (https://uptrace.dev/comparisons/datadog-vs-grafana, transcript synced 2026-07-28)
  - "Production Winston Logging: From Basic Setup to Enterprise Scale | Last9" (https://last9.io/blog/winston-logging-in-nodejs/, transcript synced 2026-07-28)
  - "Finally got observability working for Claude Code: how the hooks actually work - Reddit" (https://www.reddit.com/r/Anthropic/comments/1qd1rto/finally_got_observability_working_for_claude_code/, transcript synced 2026-07-28)
  - "How to Trace Kafka Producer-Consumer Chains with OpenTelemetry - OneUptime" (https://oneuptime.com/blog/post/2026-02-06-trace-kafka-producer-consumer-opentelemetry/view, transcript synced 2026-07-28)
  - "The Power of Asynchronous Programming in Python for Modern Backend Systems" (https://python.plainenglish.io/the-power-of-asynchronous-programming-in-python-for-modern-backend-systems-659b1808b1de, transcript synced 2026-07-28)
  - "How to Implement Distributed Tracing Context Propagation - OneUptime" (https://oneuptime.com/blog/post/2026-02-02-distributed-tracing-context-propagation/view, transcript synced 2026-07-28)
  - "Distributed Tracing Logs: How They Work & Best Practices - groundcover" (https://www.groundcover.com/learn/logging/distributed-tracing-logs, transcript synced 2026-07-28)
  - "winstonjs/winston: A logger for just about everything. - GitHub" (https://github.com/winstonjs/winston, transcript synced 2026-07-28)
  - "NotebookLM source 8fb02e97-8f8d-4dfb-8178-402906534291" (Architectural Frameworks for High-Performance Dual-Logging and Distributed Telemetry in Agentic CLI Environments, synced 2026-07-28)
  - "Trace Claude Code applications - Docs by LangChain" (https://docs.langchain.com/langsmith/trace-claude-code, transcript synced 2026-07-28)
  - "Agent hooks in Visual Studio Code (Preview)" (https://code.visualstudio.com/docs/copilot/customization/hooks, transcript synced 2026-07-28)
  - "Capturing console output in Go tests | redowan's reflections" (https://rednafi.com/go/capture-console-output/, transcript synced 2026-07-28)
  - "Could someone share an example of using memory transport and ways to listen to it? · Issue #809 · winstonjs/winston - GitHub" (https://github.com/winstonjs/winston/issues/809, transcript synced 2026-07-28)
  - "How to display structured JSON logs in Grafana Loki" (https://community.grafana.com/t/how-to-display-structured-json-logs-in-grafana-loki/157539, transcript synced 2026-07-28)
  - "How to Propagate Trace Context Across Kafka Producers and Consumers - OneUptime" (https://oneuptime.com/blog/post/2026-02-06-propagate-trace-context-kafka-producers-consumers/view, transcript synced 2026-07-28)
  - "Zero-dependency, blazing-fast regex-based PII redaction with optional compliance dashboard integration. Python package for redactpii.com - GitHub" (https://github.com/wrannaman/redact-pii-python, transcript synced 2026-07-28)
  - "Datadog LLM Observability natively supports OpenTelemetry GenAI Semantic Conventions" (https://www.datadoghq.com/blog/llm-otel-semantic-convention/, transcript synced 2026-07-28)
  - "The complete guide to OpenTelemetry in Python | LaunchDarkly | Documentation" (https://launchdarkly.com/docs/tutorials/the-complete-guide-to-python-and-opentelemetry, transcript synced 2026-07-28)
  - "Python: capture stdout and stderr in unittest - Adam Johnson" (https://adamj.eu/tech/2025/08/29/python-unittest-capture-stdout-stderr/, transcript synced 2026-07-28)
  - "Context propagation - OpenTelemetry" (https://opentelemetry.io/docs/concepts/context-propagation/, transcript synced 2026-07-28)
  - "How to Use Winston for Logging - OneUptime" (https://oneuptime.com/blog/post/2026-01-25-winston-logging-nodejs/view, transcript synced 2026-07-28)
  - "Python Logging Config: dictConfig, QueueHandler & Thread Safety - Uptrace" (https://uptrace.dev/blog/python-logging, transcript synced 2026-07-28)
  - "Environment Variables as Context Propagation Carriers - OpenTelemetry" (https://opentelemetry.io/docs/specs/otel/context/env-carriers/, transcript synced 2026-07-28)
  - "Effective Python Logging - How To Do It And Best Practices - EdgeDelta" (https://edgedelta.com/company/blog/python-logging-best-practices, transcript synced 2026-07-28)
  - "GitHub - disler/claude-code-hooks-mastery: Master Claude Code Hooks · GitHub" (https://github.com/disler/claude-code-hooks-mastery, transcript synced 2026-07-28)
  - "Streamlining Log Management with OpenTelemetry - Best Practices for Capturing, Parsing, and Storing Logs | Greptime" (https://greptime.com/blogs/2025-01-08-opentelemetry-log-management, transcript synced 2026-07-28)
  - "How to Use the OpenTelemetry Log Bridge API with Existing ..." (https://oneuptime.com/blog/post/2026-02-06-opentelemetry-log-bridge-api-logging-frameworks/view, transcript synced 2026-07-28)
  - "How to Use GenAI Semantic Conventions for LLM Monitoring - OneUptime" (https://oneuptime.com/blog/post/2026-02-06-genai-semantic-conventions-llm-monitoring/view, transcript synced 2026-07-28)
  - "Structuring Python Logs for Better Observability - Leapcell" (https://leapcell.io/blog/structuring-python-logs-for-better-observability, transcript synced 2026-07-28)
  - "pii-redactor · PyPI" (https://pypi.org/project/pii-redactor/, transcript synced 2026-07-28)
  - "Feature Request: Propagate TRACEPARENT to subprocess environments for trace hierarchy · Issue #16941 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/16941, transcript synced 2026-07-28)
  - "Pino vs. Winston: Choosing the Right Logger for Your Node.js Application - DEV Community" (https://dev.to/wallacefreitas/pino-vs-winston-choosing-the-right-logger-for-your-nodejs-application-369n, transcript synced 2026-07-28)
  - "How to Create OpenTelemetry Log Bridge API: A Complete Guide - OneUptime" (https://oneuptime.com/blog/post/2026-01-30-opentelemetry-log-bridge-api/view, transcript synced 2026-07-28)
  - "Logging Cookbook — Python 3.14.3 documentation" (https://docs.python.org/3/howto/logging-cookbook.html, transcript synced 2026-07-28)
  - "Pino Logger: Complete Node.js Guide with Examples [2026] - SigNoz" (https://signoz.io/guides/pino-logger/, transcript synced 2026-07-28)
  - "OpenTelemetry Logs [complete guide] | Uptrace" (https://uptrace.dev/opentelemetry/logs, transcript synced 2026-07-28)
  - "Propagation - OpenTelemetry" (https://opentelemetry.io/docs/languages/python/propagation/, transcript synced 2026-07-28)
  - "Pino.js: The Ultimate Guide to High-Performance Node.js Logging - Last9" (https://last9.io/blog/npm-pino-logger/, transcript synced 2026-07-28)
  - "How do I read the output of a child process without blocking in Rust? - Stack Overflow" (https://stackoverflow.com/questions/34611742/how-do-i-read-the-output-of-a-child-process-without-blocking-in-rust, transcript synced 2026-07-28)
  - "How to Use the OpenTelemetry Log Bridge API with Existing Logging Frameworks" (https://oneuptime.com/blog/post/2026-02-06-opentelemetry-log-bridge-api-logging-frameworks/view, transcript synced 2026-07-28)
  - "How to Use Environment Variables as Context Propagation Carriers - OneUptime" (https://oneuptime.com/blog/post/2026-02-06-environment-variables-context-propagation-carriers/view, transcript synced 2026-07-28)
  - "Automate workflows with hooks - Claude Code Docs" (https://code.claude.com/docs/en/hooks-guide, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: opentelemetry-logging
    - level: notebook
      id: 5afa7287-dbfe-4ae2-a716-8fd6de80d224
      title: Claude Code - Observability & Logging
      url: https://notebooklm.google.com/notebook/5afa7287-dbfe-4ae2-a716-8fd6de80d224
    - level: cluster
      id: 0
      name: https-opentelemetry-logging
    - level: source_url
      url: https://stackoverflow.com/questions/78298535/how-to-configure-tracing-subscriber-output-format-json-or-plain-text-based-on
      title: How to configure tracing_subscriber output format (json or plain text) based on env variable? - Stack Overflow
    - level: source_url
      url: https://opentelemetry.io/docs/specs/otel/logs/api/
      title: Logs API - OpenTelemetry
    - level: source_url
      url: https://github.com/open-telemetry/opentelemetry-rust
      title: open-telemetry/opentelemetry-rust - GitHub
    - level: source_url
      url: https://www.dash0.com/knowledge/opentelemetry-logging-explained
      title: How OpenTelemetry Logging Works (with Examples) - Dash0
    - level: source_url
      url: https://grafana.com/docs/loki/latest/get-started/labels/structured-metadata/
      title: What is structured metadata | Grafana Loki documentation
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/35953
      title: [FEATURE] Expose tool_use_id (and optionally W3C Baggage) as environment variables in Bash tool shell processes · Issue #35953 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://brandur.org/logfmt
      title: logfmt — brandur.org
    - level: source_url
      url: https://oneuptime.com/blog/post/2025-01-06-python-structured-logging-opentelemetry/view
      title: How to Structure Logs Properly in Python with OpenTelemetry - OneUptime
    - level: source_url
      url: https://platform.claude.com/docs/en/agent-sdk/hooks
      title: Intercept and control agent behavior with hooks - Claude API Docs
    - level: source_url
      url: https://leapcell.medium.com/gos-slog-modern-structured-logging-made-easy-b8468ac71309
      title: Go's slog: Modern Structured Logging Made Easy | by Leapcell - Medium
    - level: source_url
      url: https://www.dash0.com/guides/logging-in-python
      title: Python Logging Module: A Complete Guide - Dash0
    - level: source_url
      url: https://www.apriorit.com/dev-blog/cybersecurity-logging-python
      title: 10 Python Logging Best Practices for Cybersecurity - Apriorit
    - level: source_url
      url: https://www.redpanda.com/guides/kafka-use-cases-event-driven-architecture
      title: Event-driven architectures with Apache Kafka | Redpanda
    - level: source_url
      url: https://opentelemetry.io/docs/concepts/observability-primer/
      title: Observability primer | OpenTelemetry
    - level: source_url
      url: https://uptimerobot.com/knowledge-hub/logging/python-logging-explained/
      title: Python Logging Explained: Best Practices & Production Tips UptimeRobot Knowledge Hub
    - level: source_url
      url: https://docs.datadoghq.com/llm_observability/instrumentation/otel_instrumentation/
      title: OpenTelemetry Instrumentation - Datadog Docs
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-01-25-structured-json-logs-tracing-rust/view
      title: How to Create Structured JSON Logs with tracing in Rust - OneUptime
    - level: source_url
      url: https://outshift.cisco.com/blog/ai-ml/ai-observability-multi-agent-systems-opentelemetry
      title: AI observability in multi-agent systems using OpenTelemetry - Outshift | Cisco
    - level: source_url
      url: https://www.groundcover.com/opentelemetry/opentelemetry-logs
      title: OpenTelemetry Logs: Benefits, Concepts, & Best Practices - groundcover
    - level: source_url
      url: https://opentelemetry.io/docs/concepts/context-propagation/
      title: Context propagation - OpenTelemetry
    - level: source_url
      url: https://stackoverflow.com/questions/35520160/python-logging-performance-comparison-and-options
      title: python logging performance comparison and options - Stack Overflow
    - level: source_url
      url: https://www.growin.com/blog/event-driven-architecture-scale-systems-2025/
      title: Event Driven Architecture Done Right: How to Scale Systems with Quality in 2025 - Growin
    - level: source_url
      url: https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/
      title: Semantic conventions for generative AI metrics | OpenTelemetry
    - level: source_url
      url: https://www.shuttle.dev/blog/2024/01/09/getting-started-tracing-rust
      title: Getting Started with Tracing in Rust - Shuttle.dev
    - level: source_url
      url: https://signoz.io/guides/python-logging-best-practices/
      title: Python Logging Best Practices - Obvious and Not-So-Obvious ...
    - level: source_url
      url: https://openobserve.ai/blog/top-10-log-monitoring-tools-2025/
      title: Top 10 Log Monitoring Tools in 2025: Complete Guide - OpenObserve
    - level: source_url
      url: https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/
      title: Redirecting all kinds of stdout in Python - Eli Bendersky's website
    - level: source_url
      url: https://www.dash0.com/guides/logging-in-go-with-slog
      title: Logging in Go with Slog: A Practitioner's Guide - Dash0
    - level: source_url
      url: https://www.reddit.com/r/Python/comments/1p6qy1e/spent_a_bunch_of_time_choosing_between_loguru/
      title: Spent a bunch of time choosing between Loguru, Structlog and native logging - Reddit
    - level: source_url
      url: https://mintlify.com/shanraisshan/claude-code-best-practice/concepts/hooks
      title: Hooks - Claude Code Best Practice - Mintlify
    - level: source_url
      url: https://users.rust-lang.org/t/sending-tracing-events-to-mpsc-channel/123550
      title: Sending `tracing` events to MPSC Channel - help - Rust Users Forum
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-propagate-opentelemetry-trace-context-celery-headers/view
      title: How to Propagate OpenTelemetry Trace Context Through Celery Message Headers
    - level: source_url
      url: https://uptrace.dev/get/opentelemetry-python/propagation
      title: OpenTelemetry Trace Context Propagation [Python] - Uptrace
    - level: source_url
      url: https://docs.python.org/3/library/logging.handlers.html
      title: logging.handlers — Logging handlers — Python 3.14.3 documentation
    - level: source_url
      url: https://realpython.com/ref/best-practices/logging/
      title: logging | Python Best Practices – Real Python
    - level: source_url
      url: https://www.ebooks2go.com/img/samplefiles/9789349888289_Sample.pdf
      title: Ultimate Event-Driven Architecture with Python and Apache Kafka - eBooks2go
    - level: source_url
      url: https://www.dash0.com/guides/logging-in-node-js-with-pino
      title: Production-Grade Logging in Node.js with Pino - Dash0
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
    - level: source_url
      url: https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/
      title: Label best practices | Grafana Loki documentation - Grafana Labs
    - level: source_url
      url: https://uptrace.dev/comparisons/datadog-vs-grafana
      title: DataDog vs Grafana [2025 comparison] - Uptrace
    - level: source_url
      url: https://last9.io/blog/winston-logging-in-nodejs/
      title: Production Winston Logging: From Basic Setup to Enterprise Scale | Last9
    - level: source_url
      url: https://www.reddit.com/r/Anthropic/comments/1qd1rto/finally_got_observability_working_for_claude_code/
      title: Finally got observability working for Claude Code: how the hooks actually work - Reddit
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-trace-kafka-producer-consumer-opentelemetry/view
      title: How to Trace Kafka Producer-Consumer Chains with OpenTelemetry - OneUptime
    - level: source_url
      url: https://python.plainenglish.io/the-power-of-asynchronous-programming-in-python-for-modern-backend-systems-659b1808b1de
      title: The Power of Asynchronous Programming in Python for Modern Backend Systems
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-02-distributed-tracing-context-propagation/view
      title: How to Implement Distributed Tracing Context Propagation - OneUptime
    - level: source_url
      url: https://www.groundcover.com/learn/logging/distributed-tracing-logs
      title: Distributed Tracing Logs: How They Work & Best Practices - groundcover
    - level: source_url
      url: https://github.com/winstonjs/winston
      title: winstonjs/winston: A logger for just about everything. - GitHub
    - level: source_url
      url: https://docs.langchain.com/langsmith/trace-claude-code
      title: Trace Claude Code applications - Docs by LangChain
    - level: source_url
      url: https://code.visualstudio.com/docs/copilot/customization/hooks
      title: Agent hooks in Visual Studio Code (Preview)
    - level: source_url
      url: https://rednafi.com/go/capture-console-output/
      title: Capturing console output in Go tests | redowan's reflections
    - level: source_url
      url: https://github.com/winstonjs/winston/issues/809
      title: Could someone share an example of using memory transport and ways to listen to it? · Issue #809 · winstonjs/winston - GitHub
    - level: source_url
      url: https://community.grafana.com/t/how-to-display-structured-json-logs-in-grafana-loki/157539
      title: How to display structured JSON logs in Grafana Loki
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-propagate-trace-context-kafka-producers-consumers/view
      title: How to Propagate Trace Context Across Kafka Producers and Consumers - OneUptime
    - level: source_url
      url: https://github.com/wrannaman/redact-pii-python
      title: Zero-dependency, blazing-fast regex-based PII redaction with optional compliance dashboard integration. Python package for redactpii.com - GitHub
    - level: source_url
      url: https://www.datadoghq.com/blog/llm-otel-semantic-convention/
      title: Datadog LLM Observability natively supports OpenTelemetry GenAI Semantic Conventions
    - level: source_url
      url: https://launchdarkly.com/docs/tutorials/the-complete-guide-to-python-and-opentelemetry
      title: The complete guide to OpenTelemetry in Python | LaunchDarkly | Documentation
    - level: source_url
      url: https://adamj.eu/tech/2025/08/29/python-unittest-capture-stdout-stderr/
      title: Python: capture stdout and stderr in unittest - Adam Johnson
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-01-25-winston-logging-nodejs/view
      title: How to Use Winston for Logging - OneUptime
    - level: source_url
      url: https://uptrace.dev/blog/python-logging
      title: Python Logging Config: dictConfig, QueueHandler & Thread Safety - Uptrace
    - level: source_url
      url: https://opentelemetry.io/docs/specs/otel/context/env-carriers/
      title: Environment Variables as Context Propagation Carriers - OpenTelemetry
    - level: source_url
      url: https://edgedelta.com/company/blog/python-logging-best-practices
      title: Effective Python Logging - How To Do It And Best Practices - EdgeDelta
    - level: source_url
      url: https://github.com/disler/claude-code-hooks-mastery
      title: GitHub - disler/claude-code-hooks-mastery: Master Claude Code Hooks · GitHub
    - level: source_url
      url: https://greptime.com/blogs/2025-01-08-opentelemetry-log-management
      title: Streamlining Log Management with OpenTelemetry - Best Practices for Capturing, Parsing, and Storing Logs | Greptime
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-opentelemetry-log-bridge-api-logging-frameworks/view
      title: How to Use the OpenTelemetry Log Bridge API with Existing ...
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-genai-semantic-conventions-llm-monitoring/view
      title: How to Use GenAI Semantic Conventions for LLM Monitoring - OneUptime
    - level: source_url
      url: https://leapcell.io/blog/structuring-python-logs-for-better-observability
      title: Structuring Python Logs for Better Observability - Leapcell
    - level: source_url
      url: https://pypi.org/project/pii-redactor/
      title: pii-redactor · PyPI
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/16941
      title: Feature Request: Propagate TRACEPARENT to subprocess environments for trace hierarchy · Issue #16941 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://dev.to/wallacefreitas/pino-vs-winston-choosing-the-right-logger-for-your-nodejs-application-369n
      title: Pino vs. Winston: Choosing the Right Logger for Your Node.js Application - DEV Community
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-01-30-opentelemetry-log-bridge-api/view
      title: How to Create OpenTelemetry Log Bridge API: A Complete Guide - OneUptime
    - level: source_url
      url: https://docs.python.org/3/howto/logging-cookbook.html
      title: Logging Cookbook — Python 3.14.3 documentation
    - level: source_url
      url: https://signoz.io/guides/pino-logger/
      title: Pino Logger: Complete Node.js Guide with Examples [2026] - SigNoz
    - level: source_url
      url: https://uptrace.dev/opentelemetry/logs
      title: OpenTelemetry Logs [complete guide] | Uptrace
    - level: source_url
      url: https://opentelemetry.io/docs/languages/python/propagation/
      title: Propagation - OpenTelemetry
    - level: source_url
      url: https://last9.io/blog/npm-pino-logger/
      title: Pino.js: The Ultimate Guide to High-Performance Node.js Logging - Last9
    - level: source_url
      url: https://stackoverflow.com/questions/34611742/how-do-i-read-the-output-of-a-child-process-without-blocking-in-rust
      title: How do I read the output of a child process without blocking in Rust? - Stack Overflow
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-06-environment-variables-context-propagation-carriers/view
      title: How to Use Environment Variables as Context Propagation Carriers - OneUptime
    - level: source_url
      url: https://code.claude.com/docs/en/hooks-guide
      title: Automate workflows with hooks - Claude Code Docs
relations:
  - target: wiki/concepts/context-propagation.md
    type: related
  - target: wiki/concepts/structured-logging.md
    type: related
  - target: wiki/concepts/opentelemetry-collector.md
    type: related
---

# OpenTelemetry Logging

## Decision context

**Definition:** OpenTelemetry logging encompasses the standards, approaches, and techniques for capturing, structuring, and propagating diagnostic data within the OpenTelemetry observability framework, enabling interoperability across languages and platforms.

Synthesized from **83 contributing transcripts** in NotebookLM notebook *Claude Code - Observability & Logging*, clustered into the "https-opentelemetry-logging" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- OpenTelemetry defines a Log Data Model that standardizes how log records are represented across different programming languages and logging libraries
- Context propagation in OpenTelemetry enables trace correlation by passing context (including trace_id and span_id) through message headers or transport layers
- The OpenTelemetry Collector provides a mechanism for complex logging environments, offering a middle layer between application code and backend storage systems
- Structured JSON logging formats are preferred in OpenTelemetry pipelines since they preserve field semantics better than plain text formats
- The Log SDK approach offers a simpler setup path for capturing logs directly into the OpenTelemetry ecosystem
- Context variables (contextvars) can be used to impart contextual information into logging output in Python applications
- Hook systems in agentic CLI environments can intercept and log execution traces for post-hoc analysis of autonomous agent behavior

## Verifiable values

| Name | Value |
|---|---|
| Log entry retention (example) | `30 days` |
| File rotation threshold (example) | `1000 entries or 10MB` |
| Python version requirement (pii-redactor) | `>=3.8` |

## Related concepts

- [[context-propagation]] — Context Propagation
- [[structured-logging]] — Structured Logging
- [[opentelemetry-collector]] — OpenTelemetry Collector
- [[log-data-model]] — Log Data Model
- [[distributed-tracing]] — Distributed Tracing

## Citations (from contributing transcripts)

- **Claim:** OpenTelemetry defines a Log Data Model for standardizing log records
  - Source: Streamlining Log Management with OpenTelemetry - Best Practices for Capturing, Parsing, and Storing Logs | Greptime (`bfe65b10-b442-4640-ab28-6b1ea997c04f`)
  - Context: This blog explains how to capture logs with OpenTelemetry using the Log Data Model.
- **Claim:** Context propagation enables trace correlation through message headers
  - Source: How to Propagate OpenTelemetry Trace Context Through Celery Message Headers (`58985518-228b-4cd5-af60-a3bfd9edec7f`)
  - Context: Discusses propagating OpenTelemetry trace context through Celery message headers
- **Claim:** OpenTelemetry Collector provides a middle layer for complex environments
  - Source: Streamlining Log Management with OpenTelemetry - Best Practices for Capturing, Parsing, and Storing Logs | Greptime (`bfe65b10-b442-4640-ab28-6b1ea997c04f`)
  - Context: It covers two main approaches, the Log SDK for simple setups and the OpenTelemetry Collector for more complex environments.
- **Claim:** Structured JSON logging preserves field semantics better than plain text
  - Source: How to configure tracing_subscriber output format (json or plain text) based on env variable? - Stack Overflow (`07647ebc-c91f-4103-9238-40957db263ec`)
  - Context: Question about configuring tracing_subscriber output format (json or plain text)
- **Claim:** Hook systems in agentic CLI environments log execution traces for diagnostic analysis
  - Source: Architectural Frameworks for High-Performance Dual-Logging and Distributed Telemetry in Agentic CLI Environments (`8fb02e97-8f8d-4dfb-8178-402906534291`)
  - Context: The dual requirements of real-time user feedback and high-fidelity structured logging for post-hoc analysis create a complex engineering challenge.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `5afa7287-dbfe-4ae2-a716-8fd6de80d224`
(cluster `https-opentelemetry-logging`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Claude Code - Observability & Logging](https://notebooklm.google.com/notebook/5afa7287-dbfe-4ae2-a716-8fd6de80d224)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
