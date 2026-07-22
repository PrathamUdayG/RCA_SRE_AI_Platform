# 📋 Operational Recommendation Engine (`domain/recommendation`)

> **Welcome to the Operational Recommendation Domain!** This document serves as the onboarding guide for software engineers working on the Recommendation Engine within the Autonomous AI SRE Platform.

---

## 📌 1. Why The Recommendation Engine Exists & What Problem It Solves

In Phase 4, the **AI Root Cause Analysis Engine** identifies the primary root cause of an operational incident (e.g. Memory Thrashing caused by RAM exhaustion).

However, an incident diagnosis alone does not fix the problem. **The Operational Recommendation Engine solves this problem.** It acts as a Senior SRE advising operations teams on **what to do**, **in what priority order**, **with what safety precautions**, **validation steps**, and **rollback procedures**.

### **Difference Between RCA and Recommendations**
- **Root Cause Analysis (`domain/rca`)**: Answers *"WHAT went wrong and WHY?"* (Diagnosis).
- **Recommendations (`domain/recommendation`)**: Answers *"WHAT should we do now, HOW should we validate it, and WHAT risks are involved?"* (Guidance).
- **Remediation / Execution (Future Phase 6)**: Answers *"HOW do we execute approved actions safely?"*.

---

## 🛡️ 2. Why Recommendations Must NEVER Directly Execute Actions

A core architectural safety principle of this platform is: **Guidance is strictly decoupled from Execution.**

The Recommendation Engine produces **advisory reports only**. It MUST NEVER:
1. Execute SSH or terminal commands.
2. Restart processes or services directly.
3. Modify Kubernetes or Docker configurations automatically.

### **Why?**
- **Safety & Blast Radius Control**: Executing automated actions without policy evaluation or human verification risks widespread outages.
- **Human-in-the-Loop & Audit Compliance**: Production environments require approval gates (`requires_human_approval=True`) and risk scoring before mutation operations occur.

---

## 🔌 3. Vendor-Independent AI Gateway Architecture

Like Phase 4, the Recommendation Domain depends on `RecommendationProviderInterface` rather than a specific LLM SDK. Concrete provider adapters (e.g., `GeminiRecommendationProvider`) reside in `infrastructure/llm/`.

```text
RootCauseAnalysis (Phase 4)
           │
           ▼
 RecommendationService (application/recommendation)
           │
           ▼
 RecommendationProviderInterface (domain/recommendation)
           │
 ┌─────────┴─────────────────────┐
 ▼                               ▼
GeminiRecommendationProvider   OpenAIRecommendationProvider (Future)
(infrastructure/llm)
```

---

## 📁 4. File Inventory & Responsibilities

| File | Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **`__init__.py`** | Package Export | Exposes core Recommendation models, exceptions, and provider interface. |
| **`models.py`** | Domain Models | Pure Pydantic models (`RecommendationReport`, `Recommendation`, `ValidationStep`, `RollbackPlan`, `MonitoringRecommendation`, `PreventionRecommendation`, `RecommendationCategory`, `RecommendationPriority`, `RiskLevel`). |
| **`exceptions.py`** | Domain Exceptions | Explicit error types (`RecommendationError`, `InvalidRCAResultError`, `RecommendationProviderError`). |
| **`llm_interface.py`** | AI Gateway Contract | Abstract Base Class `RecommendationProviderInterface` decoupling recommendation logic from vendor SDKs. |
| **`README.md`** | Documentation | Onboarding guide for software engineers. |

---

## 📥 5. Inputs & Outputs

- **Input**: `RootCauseAnalysis` (produced by Phase 4 `domain/rca/models.py`).
- **Output**: `RecommendationReport` containing prioritized `Recommendation` items, `ValidationStep` entries, `RollbackPlan`, `MonitoringRecommendation` items, and `PreventionRecommendation` items.
