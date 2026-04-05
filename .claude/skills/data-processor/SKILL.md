---
name: data_processor
description: Process data efficiently
version: "1.0.0"
status: "stable"
category: utilities
triggers:
  - /data-processor
aliases:
  - /data-processor

suggest:
  - /build
  - /design
  - /nse
---

# Data Processor

Efficient data processing utility for transforming and analyzing data.

## Purpose

Process, transform, analyze, and validate data efficiently across multiple formats.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- On-demand execution (no background services)

### Technical Context
- Supports JSON, YAML, CSV, XML formats
- Streaming processing for large files
- Schema validation capabilities
- Statistical analysis features

### Architecture Alignment
- Utility tool for data operations
- Integrates with /build and /design workflows
- Supports on-demand processing only

## Your Workflow

1. Identify input format and location
2. Select appropriate action (process/analyze/transform/validate)
3. Specify output format/location if needed
4. Execute operation with streaming for large files
5. Validate results

## Validation Rules

- Verify input file exists before processing
- Check output directory is writable
- Validate schema exists when using --schema flag
- Use streaming mode for files >100MB

## Usage

```bash
/data-processor <action> [options]
```

## Actions

### `process <input> [--output <file>]`
Process input data with transformations.

**Example:**
```bash
/data-processor process data.json --output result.json
```

### `analyze <input>`
Analyze data structure and statistics.

**Example:**
```bash
/data-processor analyze data.csv
```

### `transform <input> <format>`
Transform data to specified format.

**Example:**
```bash
/data-processor transform data.json yaml
```

### `validate <input> [--schema <schema>]`
Validate data against schema.

**Example:**
```bash
/data-processor validate data.json --schema schema.json
```

## Supported Formats

- JSON
- YAML
- CSV
- XML

## Features

- Streaming processing for large files
- Schema validation
- Format conversion
- Statistical analysis
