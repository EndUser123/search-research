# TSK-behavioral-control-refactoring Data Model

## Overview
Core data structures and relationships for behavioral control architecture refactoring.

## Entities

### BehavioralControlSystem
- id: Unique system identifier
- name: System name (llm_supervisor, pre_tool_use, etc.)
- type: System type (hook, constitution, validation)
- status: Current status (active, refactoring, deprecated)
