---
title: "Please explain what cargo culting is or what cargo cult is in the context of software development."
date: "2026-02-14"
mode: "CONCISE"
uuid: "8fdce9e7-b42a-41d9-8111-c40ae7841398"
entry_count: 1
---

## Human

Please explain what cargo culting is or what cargo cult is in the context of software development.

## Assistant

Cargo culting, or cargo cult programming, refers to the practice in software development of copying code, patterns, design practices, or processes without understanding their purpose or underlying principles, often in a ritualistic way hoping it will produce desired results.[1][2]

## Origin
The term draws from real-world "cargo cults" in the South Pacific after World War II, where islanders built mock airstrips and imitated Western behaviors to attract planes delivering goods, mistaking correlation for causation. In programming, it was popularized to describe similar blind imitation.[3][15][1]

## In Programming
Developers might paste Stack Overflow snippets, add unused code (like manual deletions in garbage-collected languages), or apply design patterns rigidly without grasping why they solve specific problems. This stems from fixing bugs via trial-and-error, leaving "magical" code intact out of fear it'll break.[4][5][6][1]

## In Engineering
At a broader level, "cargo cult software engineering" involves teams mimicking successful companies' processes—like mandating overtime for "commitment" or adopting microservices, Agile rituals, or tools (Kubernetes, monorepos) without rationale—leading to inefficiency. Justification often boils down to "We've always done it this way."[2][7][9][12]

## Examples
| Context | Cargo Cult Practice | Issue |
|---------|---------------------|-------|
| Code | Adding comments to obvious code or unused imports | Bloat without value [1] |
| Architecture | Blindly using microservices for small apps | Added complexity [7][9] |
| Processes | Daily standups as status reports only | No synchronization or planning [11] |
| Tools | "At my last job we used Kafka" without need | Wrong tool for problem [9] |

## Avoidance
Understand the "why" behind practices: question tradeoffs, experiment intentionally, and prioritize principles over hype to build maintainable systems.[5][11]
