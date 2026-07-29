---
source_id: "f699cd9a-d41d-4df5-bdcf-f2fdf947299b"
title: "Top Open Source Sensitive Data Discovery Tools in 2025 - Bytebase"
notebook_id: 5afa7287-dbfe-4ae2-a716-8fd6de80d224
url: https://www.bytebase.com/blog/top-open-source-sensitive-data-discovery-tools/
type: web_page
exported: 2026-07-28
---

# Top Open Source Sensitive Data Discovery Tools in 2025 - Bytebase
How to Govern AI Agent Access to Enterprise Data

Schema Migration GUI-based, database CI/CD with GitOps

Permission-based SQL Editor Bastion-less human-to-database permission control

Dynamic Data Masking Role-based multi-level masking policy

Batch Change Multi-environments, multi-regions, multi-tenants

Use Case

Planned Database CI/CD

Just-in-Time Database Access

Adhoc Data Fix

Batch Tenant Change

Headless Database Backend

Industry

🏦 Financial Services

🌐 Technology

🏭 Manufacturing

🕹️ Gaming

🔗 Web3

Docs

Pricing

Case Study

Security

SLA

Contact

About Us

Blog Product updates and database insight Start Learning

...

Cloud

Self-host

Docs

Pricing

GitHub

Self-host

Cloud

Industry

Top Open Source Sensitive Data Discovery Tools in 2025

Tianzhou Dec 01, 2025 7 min read

Introduction

#

https://www.bytebase.com#introduction

Sensitive data discovery is the first step in protecting PII, PHI, and other regulated information. Before you can mask, encrypt, or restrict access to sensitive data, you need to find it.

Open source tools for this task span a spectrum:

NLP libraries

 - Building blocks for custom detection pipelines

Lightweight CLI scanners

 - Quick, targeted scans for developers and CI pipelines

Full data platforms

 - Comprehensive metadata management with classification as one feature

This article covers four tools across this spectrum, from NLP foundations to enterprise data catalogs with built-in classification.

spaCy

#

https://www.bytebase.com#spacy

spaCy

https://www.bytebase.com#spacy

 is the industrial-strength NLP library that powers many sensitive data detection tools.

spaCy provides named entity recognition (NER) that can identify persons, organizations, locations, and other entity types in text. Both PiiCatcher and OpenMetadata use spaCy under the hood for ML-based PII detection. If you need maximum flexibility, you can build custom detection pipelines directly with spaCy, though the tools below provide ready-to-use solutions.

PiiCatcher

#

https://www.bytebase.com#piicatcher

PiiCatcher

https://www.bytebase.com#piicatcher

 is a focused CLI scanner that detects PII in databases and tags findings in data catalogs.

Detection approach:

 PiiCatcher uses two methods - regex pattern matching against column names, and NLP-based analysis of sample data using spaCy. This dual approach catches both obviously-named columns (e.g.,  email ,  ssn ) and columns with generic names but sensitive content.

Data source support:

 PostgreSQL, MySQL, SQLite, Redshift, Athena, Snowflake, BigQuery.

Key strength:

 Native integration with data catalogs. PiiCatcher can automatically tag discovered PII in DataHub or Amundsen, bridging the gap between standalone scanning and catalog-based governance.

Best for:

 Teams wanting a lightweight scanner that feeds into their existing data catalog.

Hawk-Eye

#

https://www.bytebase.com#hawk-eye

Hawk-Eye

https://www.bytebase.com#hawk-eye

 is a broad-spectrum scanner covering databases, cloud storage, and files - including images and videos via OCR.

Detection approach:

 Pattern matching with configurable fingerprints defined in YAML. Supports OCR for images and documents (350+ file types including DOCX, PDF, images, videos).

Data source support:

 MySQL, PostgreSQL, MongoDB, CouchDB, Redis, S3, Google Cloud Storage, Firebase, Slack, Google Drive, local filesystem.

Key strength:

 Breadth of coverage. Unlike database-only scanners, Hawk-Eye finds PII across your entire data footprint - useful when sensitive data leaks into unstructured storage.

Best for:

 Security teams auditing diverse data sources beyond just databases.

OpenMetadata

#

https://www.bytebase.com#openmetadata

OpenMetadata

https://www.bytebase.com#openmetadata

 is a unified metadata platform with auto-classification as a core governance feature.

Detection approach:

 Auto-Classification workflow powered by spaCy with configurable confidence levels (0-100). The system identifies PII and either auto-applies tags or suggests them for review. Runs as a separate workflow from metadata ingestion, so you can tune classification independently.

Data source support:

 84+ connectors spanning databases, dashboards, messaging, and pipelines.

Key strength:

 Tight integration between classification and governance workflows. Tags flow into data quality rules, access policies, and team collaboration features. The no-code profiler makes classification accessible to non-engineers.

Best for:

 Teams wanting a modern, API-first platform where classification drives downstream governance policies.

Alternative:

DataHub

https://www.bytebase.com#openmetadata

 is another open-source metadata platform, but its auto-classification feature only supports Snowflake and has been 

marked as deprecated

https://docs.datahub.com/docs/metadata-ingestion/docs/dev_guides/classification

. If you're using DataHub, consider pairing it with PiiCatcher for broader classification coverage.

Comparison

#

https://www.bytebase.com#comparison

Tool Language Primary Use Case Detection Method Data Source Support Deployment License

spaCy

Python NLP library / building block Named entity recognition (NER), ML models N/A (text processing only) pip MIT

PiiCatcher

Python CLI scanner for databases Regex + NLP (spaCy) PostgreSQL, MySQL, SQLite, Redshift, Athena, Snowflake, BigQuery pip, Docker Apache 2.0

Hawk-Eye

Python Multi-source scanner (DBs, cloud, files) Pattern matching + OCR MySQL, PostgreSQL, MongoDB, Redis, S3, GCS, Firebase, Slack pip, Docker LGPL 2.1 + Commons Clause

OpenMetadata

Java / Python Data platform with governance Auto-classification workflow (spaCy), confidence thresholds 84+ connectors Docker, Kubernetes Apache 2.0  

Choose based on your needs:

spaCy

 - Build custom detection pipelines with maximum flexibility

PiiCatcher

 - Catalog-integrated database scanning

Hawk-Eye

 - Broad coverage across databases, cloud storage, and files

OpenMetadata

 - Classification within a full metadata platform

Start lightweight, then graduate to full platforms as governance requirements grow.

From Discovery to Protection

#

https://www.bytebase.com#from-discovery-to-protection

Finding sensitive data is only half the challenge - you then need to protect it. 

Bytebase provides dynamic data masking

https://docs.bytebase.com/security/data-masking/overview

 that can be driven by classification results.

Once you've identified PII columns using tools above, you can call the Bytebase REST/gRPC API to apply masking policies programmatically. This creates an automated pipeline: scan → classify → mask, ensuring discovered sensitive data is protected without manual intervention.

All-in-One Database Workflows

Schema migration, data fix, just-in-time access, data masking, and audit logging in one place.

💡 Learn more

https://docs.bytebase.com/security/data-masking/overview

Related posts

Back to blog

https://docs.bytebase.com/security/data-masking/overview

Explanation

https://docs.bytebase.com/security/data-masking/overview

From Schema as Code to Schema as Context

Tianzhou Mar 03, 2026

Engineering

https://docs.bytebase.com/security/data-masking/overview

How to Fix Slow MySQL Queries: A Practical Guide

Adela Mar 03, 2026

Engineering

https://docs.bytebase.com/security/data-masking/overview

Database Blue-Green Deployment: A Practical Guide

Adela Feb 28, 2026

COMPARISONS

vs. Liquibase

https://docs.bytebase.com/security/data-masking/overview

vs. Flyway

https://docs.bytebase.com/security/data-masking/overview

vs. DataGrip

https://docs.bytebase.com/security/data-masking/overview

vs. DBeaver

https://docs.bytebase.com/security/data-masking/overview

vs. CloudBeaver

https://docs.bytebase.com/security/data-masking/overview

vs. Navicat

https://docs.bytebase.com/security/data-masking/overview

vs. Metabase

https://docs.bytebase.com/security/data-masking/overview

vs. schemachange

https://docs.bytebase.com/security/data-masking/overview

vs. Jira

https://docs.bytebase.com/security/data-masking/overview

PRODUCT

Pricing

https://docs.bytebase.com/security/data-masking/overview

Changelog

https://docs.bytebase.com/security/data-masking/overview

Documentation

https://docs.bytebase.com/security/data-masking/overview

API

https://docs.bytebase.com/security/data-masking/overview

Supported Databases

https://docs.bytebase.com/security/data-masking/overview

Security

https://docs.bytebase.com/security/data-masking/overview

RESOURCES

Resources

https://docs.bytebase.com/security/data-masking/overview

Terms

https://docs.bytebase.com/security/data-masking/overview

Policy

https://docs.bytebase.com/security/data-masking/overview

Partners

https://docs.bytebase.com/security/data-masking/overview

COMPANY

About

https://docs.bytebase.com/security/data-masking/overview

Brand

https://docs.bytebase.com/security/data-masking/overview

Contact

https://docs.bytebase.com/security/data-masking/overview

Bytebase Logo

https://docs.bytebase.com/security/data-masking/overview

Github

https://docs.bytebase.com/security/data-masking/overview

Discord

https://docs.bytebase.com/security/data-masking/overview

Twitter

https://docs.bytebase.com/security/data-masking/overview

Youtube

https://docs.bytebase.com/security/data-masking/overview

LinkedIn

https://docs.bytebase.com/security/data-masking/overview

©  2026  Bytebase. All Rights Reserved.
