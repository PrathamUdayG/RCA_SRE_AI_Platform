# 🔍 Investigation Domain Package (`domain/investigation`)

> **Welcome to the Investigation Planning Engine!** This document serves as the onboarding guide for software engineers working on the Investigation Domain within the Autonomous AI SRE Platform.

---

## 📌 1. Why This Folder Exists & What Problem It Solves

In early prototypes (Phase 0), when a user asked a question like *"Why is my server slow?"*, the system attempted to pick and run a single isolated command (`free -m` or `top`). 

However, real-world SRE (Site Reliability Engineering) incident investigations require multi-faceted diagnostic plans. A slow server might be caused by CPU saturation, memory exhaustion, disk I/O bottlenecks, or network degradation.

**This folder (`domain/investigation`) solves that problem.** It decouples **Investigation Planning** from **Execution**. Its sole responsibility is to translate a user's natural language question into a structured, validated `InvestigationPlan` without running any commands or making remote network calls.

---

## 🏗️ 2. Where It Fits in the AI SRE Platform

The platform operates in clean, decoupled architectural phases:

```text
Natural Language Question
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│ PHASE 1: Investigation Planning Engine                    │
│ (domain/investigation)                                   │
│ Output: InvestigationPlan                                │
└───────────────────────────┬──────────────────────────────┘
                            │  (Pure Domain Plan - No SSH)
                            ▼
┌──────────────────────────────────────────────────────────┐
│ FUTURE PHASE 2: Investigation Execution Engine          │
│ Executes steps via SSH, logs to DB, parses stdout         │
└───────────────────────────┬──────────────────────────────┘
                            │  (Collected Metrics)
                            ▼
┌──────────────────────────────────────────────────────────┐
│ FUTURE PHASE 3: Root Cause Analysis (RCA) Engine         │
│ Synthesizes metrics into incident diagnosis              │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 3. File Inventory & Responsibilities

| File | Type / Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **`__init__.py`** | Package Export | Exposes clean public imports (`InvestigationPlanner`, `InvestigationPlan`, etc.). |
| **`models.py`** | Domain Models | Pure Pydantic data schemas (`InvestigationPlan`, `InvestigationStep`, `InvestigationPriority`, `ExecutionStrategy`). **Contains NO logic.** |
| **`exceptions.py`** | Domain Exceptions | Explicit error hierarchy (`InvalidQuestionError`, `PlanGenerationError`, `TemplateNotFoundError`). |
| **`template_registry.py`** | Domain Data | Standardized diagnostic templates for incident patterns (Slow Server, High Memory, High CPU, Disk Full, Network). |
| **`rule_engine.py`** | Business Logic | Rule matcher evaluating natural language question keywords against templates and priority levels. |
| **`strategy.py`** | Business Logic | Evaluates step dependencies to assign `SEQUENTIAL` vs `PARALLEL` execution strategies and time duration estimates. |
| **`planner.py`** | Domain Orchestrator | Main entry point (`InvestigationPlanner`) assembling rules, templates, and strategies into a validated `InvestigationPlan`. |
| **`README.md`** | Documentation | Onboarding documentation for engineers. |

---

## ⚠️ 4. Critical Architectural Rules

> [!IMPORTANT]
> 1. **NO SSH EXECUTION**: No file in this directory may ever import `paramiko`, connect to SSH, or execute commands on remote servers.
> 2. **NO LLM CALLS**: Planning logic in Phase 1 relies on deterministic rules, templates, and intent matchers. External API calls to Gemini or OpenAI belong in higher-level application services.
> 3. **NO DATABASE OPERATIONS**: This package must not read from or write to PostgreSQL or any storage layer.
> 4. **PURE DOMAIN LOGIC**: All classes in this package must be deterministic, highly testable unit-tested Python modules.

---

## 🗺️ 5. Future Roadmap

- **Phase 1.1**: Dynamic LLM-driven plan expansion for novel, unseen incident symptoms.
- **Phase 1.2**: Custom user-defined template registration via API.
- **Phase 1.3**: Advanced dependency graph validation for complex DAG step dependencies.
