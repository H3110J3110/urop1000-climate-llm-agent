# UROP1000: Agentic LLM Applications for Climate Science

**Focus:** Building and customizing LLM agents for climate data retrieval and analysis using LangGraph/LangChain.

---

## Project Overview

This project explores agentic LLM workflows for climate science applications. The goal is to develop agents that can autonomously retrieve climate data, perform analysis, and generate actionable insights. Core technologies include LangGraph, LangChain, and Python.

---

## Current Status

| Week | Focus | Status |
|------|-------|--------|
| 1 | Onboarding: Agents, DeepAgents, Middleware | Completed |
| 2 | More LangChain tutorials + customization exercises | In progress |

**Completed:**
- ✅ Tutorial 1: Custom tool integration (Slack/ Discord replacement)
- ✅ Tutorial 2: LangChain basics
- ⏳ Tutorial 3: Image generation (blocked on Gemini API – fallback in progress)

**Next:**
- Complete Tutorial 3 with image generation model
- Middleware customization exercises
- Begin project-specific agent development

---

## Weekly Log

<details>
<summary><b>Week 1 (Jun 3 to Jun 10)</b></summary>

<br>

### Week 1

**Readings completed:**
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents) – Core concepts of agent architecture
- [Agent Harnesses / DeepAgents Overview](https://docs.langchain.com/oss/python/deepagents/overview) – Framework for building deployable agents
- [DeepAgents Customization](https://docs.langchain.com/oss/python/deepagents/customization) – Architecture and extension points
- [Middleware Customization](https://docs.langchain.com/oss/python/langchain/middleware/custom) – How to modify agent behavior at pipeline level

**Key concepts learned:**
- Agents = LLM + tools + reasoning loop
- DeepAgents = harness for deploying agents with middleware support
- Middleware = hooks for logging, rate limiting, error handling, etc.

**Tutorial(s) completed:**
1. [Data analysis](https://docs.langchain.com/oss/python/deepagents/data-analysis) – replaced Slack with Discord, built custom tool wrapper
2. [Deep research](https://docs.langchain.com/oss/python/deepagents/deep-research) – chains, prompts, output parsers

**Blockers encountered:**
- Tutorial 3 requires Gemini API for image generation – currently region-blocked
- Fallback plan: use OpenRouter (pending)

**Goals for next week:**
- Complete Tutorial 3 with fallback approach
- Complete middleware customization exercises (pending supervisor-provided materials)
- Practice Git branching and PR workflow for documentation/collaboration

---
</details>


## Setup (TBD)

*Will be updated as the project progresses.*
