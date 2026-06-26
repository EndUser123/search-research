# Risk Policy Documentation

This directory contains documentation for the risk policy system.

## Overview

The risk policy system is designed to provide guardrails and controls for agent actions based on the potential impact of those actions. It helps to prevent unintended consequences by classifying tasks into different risk tiers and enforcing specific workflows or verifications for higher-risk operations.

## Risk Tiers

Tasks are categorized into the following risk tiers:

*   **LOW**: Actions with minimal impact, typically read-only operations, non-critical file modifications, or changes confined to development environments. These tasks often proceed with minimal friction.
*   **MED**: Actions that involve modifications to application code, configuration, or data that could affect functionality, performance, or user experience. These tasks usually require planning and verification steps.
*   **HIGH**: Actions with significant potential impact, such as infrastructure changes, security-related modifications, production deployments, or destructive operations. These tasks require a more stringent workflow, including detailed planning, explicit verification, and often manual approval/application.

## Policy Controls

Each risk tier has associated policy controls that dictate the agent's workflow:

*   **LOW**: Fast path, minimal intervention.
*   **MED**: Requires a clear plan and verification of changes.
*   **HIGH**: Requires a detailed plan, explicit verification, and typically a manual application step by a human to ensure safety and prevent automated destructive actions.

## Usage

The agent automatically assesses the risk tier of a given task based on keywords, file paths, and commands. Users can be guided through the appropriate workflow depending on the determined risk level. The system provides feedback on the active risk tier and what controls are in place.