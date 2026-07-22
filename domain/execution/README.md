# ⚡ Execution Domain Package (`domain/execution`)

> **Welcome to the Multi-Command Execution Domain!** This document provides onboarding guidance for software engineers working on the Execution Domain within the Autonomous AI SRE Platform.

---

## 📌 1. Why The Execution Domain Exists & What Problem It Solves

In Phase 1, the **Investigation Planning Engine** produces an `InvestigationPlan` containing diagnostic steps (e.g. CPU load, Memory breakdown, Disk usage, Process tree). 

However, an investigation plan is just a blueprint. **The Execution Domain defines the data models, contracts, and error abstractions required to run an investigation plan and record standardized results.**

### **Difference Between Planning & Execution**
- **Planning (`domain/investigation`)**: Answers *"WHAT diagnostic observations should we make?"* without connecting to any server or executing commands.
- **Execution (`domain/execution` & `application/execution`)**: Answers *"HOW do we run those diagnostic steps reliably?"* by connecting via SSH, invoking whitelisted commands, logging audit records, parsing terminal text, handling step timeouts, and collecting aggregated metrics.

---

## 🏗️ 2. Where It Fits in the AI SRE Platform

```text
User Natural Language Question
               │
               ▼
┌────────────────────────────────────────┐
│ Phase 1: Investigation Planning Engine │
│ Output: InvestigationPlan              │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Phase 2: Multi-Command Execution Engine│
│ (domain/execution & app/execution)    │
│ Output: InvestigationExecutionResult   │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Future Phase 3: Correlation Engine     │
│ (Root Cause Analysis & Diagnosis)      │
└────────────────────────────────────────┘
```

---

## 📁 3. File Inventory & Responsibilities

| File | Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **`__init__.py`** | Package Export | Exposes core execution models and exceptions cleanly. |
| **`models.py`** | Domain Models | Pure Pydantic models (`StepExecutionResult`, `ExecutionMetrics`, `InvestigationExecutionResult`, `ExecutionStatus`). **Contains NO logic.** |
| **`exceptions.py`** | Domain Exceptions | Error hierarchy (`ExecutionError`, `CommandNotFoundError`, `StepExecutionError`, `TimeoutExecutionError`). |
| **`README.md`** | Documentation | Onboarding guide for new software engineers. |

---

## 📥 4. Inputs & Outputs

- **Input**: `InvestigationPlan` (from Phase 1 `domain/investigation/models.py`).
- **Output**: `InvestigationExecutionResult` containing ordered `StepExecutionResult` objects and aggregated `ExecutionMetrics`.

---

## ⚠️ 5. Architectural Constraints

> [!IMPORTANT]
> 1. **NO AI REASONING OR RCA**: The execution engine collects metrics and raw outputs. It MUST NOT attempt to diagnose root causes or call LLMs.
> 2. **STANDARDIZED DATA**: All execution outcomes (Success, Partial Failure, Timeout) must produce valid `StepExecutionResult` structures so downstream correlation engines receive clean data.
> 3. **ISOLATION**: Domain models in `domain/execution/models.py` contain schema definitions only and must not import network or SSH modules.
