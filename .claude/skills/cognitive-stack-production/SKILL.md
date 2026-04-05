---
name: cognitive_stack_production
description: Production deployment command for Cognitive-Stack Framework integration
category: orchestration
version: 1.0.0
status: stable
triggers:
  - /cognitive-stack-production
aliases:
  - /cognitive-stack-production

suggest:
  - /cognitive-stack
  - /qa
  - /deploy
---

# Cognitive-Stack Production Deployment

Production deployment command for Cognitive-Stack Framework integration.

## Purpose

Manage production deployment workflows for Cognitive-Stack Framework including deploy, validate, rollback, and status operations.

## Project Context

### Constitution/Constraints
- **Best Long-Term Solution First** - Implement proper deployment patterns
- **Evidence-First** - Validate deployment readiness before executing
- **User Control** - All deployments require explicit user initiation

### Technical Context
- Production deployment workflows
- Pre-deployment validation checks
- Rollback capability to previous versions
- Environment management (dev, staging, production)

### Architecture Alignment
- Works with `/cognitive-stack`, `/qa`, `/deploy`
- Extends framework management to production context

## Your Workflow

### `deploy [--environment <env>]`
1. Validate production readiness
2. Check environment configuration
3. Execute deployment to specified environment
4. Verify deployment succeeded

### `validate`
1. Run pre-deployment validation checks
2. Verify all dependencies present
3. Check configuration integrity
4. Report readiness status

### `rollback [--version <version>]`
1. Verify target version exists
2. Stop current deployment
3. Restore previous version
4. Verify rollback succeeded

### `status`
1. Check current deployment version
2. Verify deployment health
3. Display environment information

## Validation Rules

### Prohibited Actions

- Do NOT deploy without validation
- Do NOT deploy to production without explicit environment specification
- Do NOT rollback without verifying target version exists
- Do NOT skip pre-deployment checks

## Usage

```bash
/cognitive-stack-production <action> [options]
```

## Actions

### `deploy [--environment <env>]`
Deploy to production with specified environment.

**Example:**
```bash
/cognitive-stack-production deploy --environment production
```

### `validate`
Validate production readiness.

**Example:**
```bash
/cognitive-stack-production validate
```

### `rollback [--version <version>]`
Rollback to previous version.

**Example:**
```bash
/cognitive-stack-production rollback --version 1.2.0
```

### `status`
Check production deployment status.

**Example:**
```bash
/cognitive-stack-production status
```

## Features

- Production deployment workflows
- Pre-deployment validation
- Rollback capability
- Environment management
