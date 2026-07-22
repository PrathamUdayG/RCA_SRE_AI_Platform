# 🔗 Data Correlation Engine (`domain/correlation`)

> **Welcome to the Data Correlation Engine!** This document provides onboarding guidance for software engineers working on the Correlation Domain within the Autonomous AI SRE Platform.

---

## 📌 1. Why The Correlation Engine Exists & What Problem It Solves

In Phase 2, the **Multi-Command Execution Engine** produces raw observations (e.g. `CPU Load = 4.2`, `RAM = 91% used`, `Swap = 200MB used`, `Disk = 92%`). 

However, raw metrics are individual observations. A single high metric does not tell an SRE the operational story. 

**The Data Correlation Engine solves this problem.** It evaluates relationships across independent diagnostic observations and synthesizes them into structured **Operational Findings** supported by empirical **Evidence**.

### **Difference Between Execution and Correlation**
- **Execution (`domain/execution`)**: Answers *"What raw metrics did the server report?"* (e.g., `free -m` stdout).
- **Correlation (`domain/correlation`)**: Answers *"What operational patterns do these metrics form when combined?"* (e.g., High RAM + Active Swap = Memory Saturation).
- **RCA / Diagnosis (Future Phase 4)**: Answers *"Why did this incident happen and how do we remediate it?"*.

---

## 🏗️ 2. Why Correlation Is Required Before AI Reasoning

Sending unstructured terminal logs directly to an LLM leads to hallucination, inconsistent severity ratings, and ungrounded diagnoses.

By introducing a **Deterministic Rule-Based Correlation Engine** before AI reasoning:
1. **Empirical Evidence**: Every finding contains concrete, mathematical evidence (`metric_name`, `observed_value`, `threshold`).
2. **Rule-Based Confidence**: Confidence scores (`0.95`, `0.92`) are calculated algorithmically based on deterministic thresholds rather than LLM guesswork.
3. **Structured Context for LLM**: Phase 4 Root Cause Analysis receives structured, validated operational findings rather than thousands of lines of raw terminal stdout.

---

## 📁 3. File Inventory & Responsibilities

| File | Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **`__init__.py`** | Package Export | Exposes core correlation models, exceptions, and rules cleanly. |
| **`models.py`** | Domain Models | Pure Pydantic models (`CorrelationResult`, `Finding`, `Evidence`, `Severity`, `FindingCategory`). **Contains NO logic.** |
| **`exceptions.py`** | Domain Exceptions | Explicit error hierarchy (`CorrelationError`, `InvalidExecutionResultError`, `RuleEvaluationError`). |
| **`rules/base_rule.py`** | Abstract Contract | Abstract base class `BaseCorrelationRule` defining the interface for all domain rules. |
| **`rules/cpu_rules.py`** | Domain Rules | Correlates load averages with top CPU processes to detect CPU saturation. |
| **`rules/memory_rules.py`** | Domain Rules | Correlates RAM usage with swap activity to detect memory pressure. |
| **`rules/disk_rules.py`** | Domain Rules | Evaluates filesystem storage usage percentages against capacity thresholds. |
| **`rules/network_rules.py`** | Domain Rules | Evaluates open listening sockets and network stack activity. |
| **`rules/process_service_rules.py`**| Domain Rules | Detects failed systemd services and process state anomalies. |
| **`rules/container_rules.py`**| Domain Rules | Detects crashed Docker containers or Kubernetes pod failures. |
| **`README.md`** | Documentation | Onboarding guide for new software engineers. |

---

## 📥 4. Inputs & Outputs

- **Input**: `InvestigationExecutionResult` (produced by Phase 2 `domain/execution/models.py`).
- **Output**: `CorrelationResult` containing structured `Finding` items and empirical `Evidence` lists.

---

## ⚠️ 5. Architectural Constraints

> [!IMPORTANT]
> 1. **NO LLM OR AI CALLS**: The Correlation Engine is 100% deterministic and rule-based. It MUST NOT call external LLM APIs or Gemini.
> 2. **NO SSH OR NETWORK CALLS**: All evaluation is performed in-memory on Phase 2 `InvestigationExecutionResult` payloads.
> 3. **HIGH MODULARITY**: Rules are decoupled into domain modules (`cpu_rules.py`, `memory_rules.py`, `disk_rules.py`). New rules can be added without modifying existing rule files.
