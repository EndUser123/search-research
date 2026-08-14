---
title: "andrej karpathy"
date: "2025-12-13"
mode: "COPILOT"
uuid: "ae14fcef-1f6b-4886-9120-42c700b2e13c"
entry_count: 2
---

## Human

andrej karpathy

## Assistant

Andrej Karpathy is a prominent AI researcher known for his work in deep learning, computer vision, and large language models.[1][2]

## Background
Born in 1986, Karpathy earned his PhD from Stanford University in 2015 under Fei-Fei Li, focusing on convolutional and recurrent neural networks for vision and language tasks. He gained early recognition through YouTube tutorials on Rubik's cube solving under the channel badmephisto. His academic contributions include highly cited papers like those on ImageNet classification and video understanding.[2][6]

## Career Highlights
Karpathy co-founded OpenAI in 2015 as a research scientist, then served as Tesla's Director of AI from 2017 to 2022, leading the Autopilot vision team on data labeling, neural nets, and deployment. In 2023-2024, he returned briefly to OpenAI for midtraining and synthetic data work. He founded Eureka Labs in 2024 to advance AI education, launching courses like LLM101n and the "Zero to Hero" series.[3][1][2]

## Key Contributions
He created and taught Stanford's influential CS231n course on convolutional neural networks, which grew massively in popularity. Karpathy popularized concepts like "vibe coding" in 2025 for AI-assisted app building and maintains active YouTube content on LLMs. His GitHub and blog offer practical neural net training advice, with repositories followed by over 125,000 users.[4][7][8][2]

## Human

I recently saw a video where he was talking about a prompting technique related to asking about how a group of people would want the request answered.  Can you figure out what Im' talking about?

## Assistant

You are almost certainly thinking of Karpathy’s “LLMs as simulators” prompt pattern: instead of asking the model what *it* thinks, you ask what a *group of people* would say about your question.[1][2][3]

## The core idea

Karpathy’s advice is: don’t treat the LLM as a single entity with its own opinion; treat it as a simulator of many possible people.  So instead of prompts like “What do you think about X?”, you ask things like “What would be a good group of people to explore X? What would they say?”.  This nudges the model to surface multiple perspectives (e.g., an optimistic researcher, a pessimistic researcher, a regulator, a founder) rather than one safe, averaged answer.[2][4][3][5][1]

## Example prompt pattern

The technique often looks like:

- First: “What would be a good group of people to explore topic X?” (model proposes personas).[6][1]
- Then: “Now simulate a panel discussion among those people and have each one give their view.”[3][1]

Variants people highlight inspired by his post include prompts such as: “If an optimistic and a pessimistic AI researcher debated the future of AI, what arguments would each make?” or “If a critical editor, empathetic copywriter, and data-driven marketer reviewed this text, what would each point out?”.[4][3]

## Why it works

This framing exploits the model’s strength at role simulation instead of forcing it into a fake “self” with a single opinion.  It also tends to bypass some of the blandness from RLHF by asking for contrasting viewpoints, which leads to richer, more informative outputs for exploration, design, and decision-making.[2][3][6]
