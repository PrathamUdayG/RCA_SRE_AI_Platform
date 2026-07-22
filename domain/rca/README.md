# 🧠 AI Root Cause Analysis Engine (`domain/rca`)

> **Welcome to the AI Root Cause Analysis Domain!** This document serves as the onboarding guide for software engineers working on the AI RCA Engine within the Autonomous AI SRE Platform.

---

## 📌 1. Why The RCA Engine Exists & What Problem It Solves

In Phase 3, the **Data Correlation Engine** groups raw observations into structured **Operational Findings** (e.g. Memory Pressure, Disk Warning, CPU Saturation) backed by empirical **Evidence**.

However, findings alone do not synthesize the ultimate root cause. **The AI Root Cause Analysis Engine solves this problem.** It acts as a Senior SRE reasoning engine that analyzes correlated findings, formulates competing hypotheses, identifies affected components, and produces an authoritative incident diagnosis.

### **Difference Between Correlation and RCA**
- **Correlation (`domain/correlation`)**: Answers *"What metric anomalies co-occurred?"* (e.g., RAM at 92% + Swap actively used).
- **RCA (`domain/rca`)**: Answers *"What underlying fault caused these co-occurring anomalies?"* (e.g., Memory leak in application process leading to swap thrashing and CPU slowdown).

---

## 🛡️ 2. Why AI Reasons Over Structured Evidence (Not Raw Terminal Output)

A core design principle of this platform is: **The LLM never receives raw terminal stdout, unparsed logs, or SSH text.**

Sending raw terminal output to LLMs leads to:
1. **Hallucinations & Context Bloat**: Unparsed text overwhelms context windows with irrelevant noise.
2. **Ungrounded Reasoning**: LLMs guess root causes without mathematical metric validation.

By passing only structured `CorrelationResult` payloads:
- **100% Grounded Reasoning**: Every hypothesis MUST link to concrete `Evidence` items (`metric_name`, `observed_value`, `threshold`).
- **Deterministic Gateway**: Prompts enforce structured JSON schemas.

---

## 🔌 3. Vendor-Independent AI Gateway Architecture

The RCA Domain depends on `LLMProviderInterface` rather than a specific LLM SDK. Concrete provider adapters (e.g., `GeminiRCAProvider`, `OpenAIRCAProvider`, `ClaudeRCAProvider`) reside in `infrastructure/llm/`.

```text
CorrelationResult (Phase 3)
           │
           ▼
  RCAService (application/rca)
           │
           ▼
 LLMProviderInterface (domain/rca)
           │
 ┌─────────┴──────────┐
 ▼                    ▼
GeminiRCAProvider   OpenAIRCAProvider (Future)
(infrastructure/llm)
```

---

## 📁 4. File Inventory & Responsibilities

| File | Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **`__init__.py`** | Package Export | Exposes core RCA models, exceptions, and provider interface. |
| **`models.py`** | Domain Models | Pure Pydantic models (`RootCauseAnalysis`, `Hypothesis`, `SupportingEvidence`, `ReasoningTrace`, `AffectedComponent`, `AnalysisMetadata`). |
| **`exceptions.py`** | Domain Exceptions | Explicit error types (`RCAError`, `InvalidCorrelationResultError`, `LLMProviderError`). |
| **`llm_interface.py`** | AI Gateway Contract | Abstract Base Class `LLMProviderInterface` decoupling RCA logic from vendor SDKs. |
| **`README.md`** | Documentation | Onboarding guide for software engineers. |

---

## 📥 5. Inputs & Outputs

- **Input**: `CorrelationResult` (produced by Phase 3 `domain/correlation/models.py`).
- **Output**: `RootCauseAnalysis` containing `primary_root_cause`, `overall_confidence`, `primary_hypothesis`, `alternative_hypotheses`, and `reasoning_trace`.
