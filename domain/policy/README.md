# 🛡️ Policy Engine & Approval Framework (`domain/policy`)

> **Welcome to the Policy Engine & Approval Framework Domain!** This document serves as the onboarding guide for software engineers working on the Policy Domain within the Autonomous AI SRE Platform.

---

## 📌 1. Why The Policy Engine Exists & What Problem It Solves

In Phase 5, the **Operational Recommendation Engine** formulates guidance (e.g. Restart Service, Increase Memory Limit, Inspect Process Tree).

However, an AI recommendation is just an advice payload. **The Policy Engine is the safety perimeter of the AI SRE Platform.** It evaluates every recommendation against strict organizational security policies before any execution or autonomous remediation can occur.

### **Difference Between Recommendation and Policy Decision**
- **Recommendation (`domain/recommendation`)**: Answers *"What SHOULD we do to fix this incident?"* (Advisory).
- **Policy Decision (`domain/policy`)**: Answers *"Is this recommended action SAFE, PROHIBITED, AUTO-APPROVED, or requiring HUMAN APPROVAL?"* (Governance & Enforcement).
- **Autonomous Remediation (Future Phase 7)**: Executes only those actions granted `AUTO_APPROVED` or explicit human approval.

---

## 🔒 2. Why Recommendations Should Never Directly Execute Actions

In production operations, executing unvalidated AI recommendations poses severe risks:
- **Blast Radius Escalation**: An AI might recommend restarting a critical database master node during peak traffic.
- **Security & Compliance Violations**: Unchecked actions could alter firewall rules, expose sensitive ports, or delete unbacked-up storage volumes.
- **Uncontrolled Cascading Failures**: Restarting dependent services simultaneously can trigger thundering herd outages.

**The Policy Engine guarantees that every recommendation passes through deterministic, rule-based permission boundaries.**

---

## 🚦 3. Approval Statuses & Permission Matrix

| Approval Status | Execution Permission | Description | Required Authorized Role |
| :--- | :--- | :--- | :--- |
| **`AUTO_APPROVED`** | `ALLOWED_AUTOMATED` | Read-only inspection, diagnostic queries, or low-risk safe actions. | Automated SRE System |
| **`HUMAN_APPROVAL_REQUIRED`** | `ALLOWED_MANUAL_ONLY` | Production mutations (service restarts, pod scaling, config edits). | Senior SRE / DevOps |
| **`CRITICAL_APPROVAL_REQUIRED`**| `ALLOWED_MANUAL_ONLY` | High-impact changes to databases or storage volumes. | Principal SRE / Tech Lead |
| **`SECURITY_APPROVAL_REQUIRED`**| `ALLOWED_MANUAL_ONLY` | Firewall, network routing, or security policy alterations. | Security Administrator |
| **`PROHIBITED`** | `BLOCKED` | Destructive operations (e.g., `rm -rf /`, unvalidated data purges). | None (Blocked) |

---

## 📁 4. File Inventory & Responsibilities

| File | Layer | Primary Responsibility |
| :--- | :--- | :--- |
| **`__init__.py`** | Package Export | Exposes core Policy models, exceptions, and rules cleanly. |
| **`models.py`** | Domain Models | Pure Pydantic models (`PolicyDecision`, `ApprovalRequest`, `ApprovalStatus`, `ActionPermission`, `PolicyViolation`, `PolicyRule`, `RiskLevel`, `DecisionMetadata`). |
| **`exceptions.py`** | Domain Exceptions | Explicit error hierarchy (`PolicyError`, `InvalidRecommendationReportError`, `PolicyRuleEvaluationError`). |
| **`rules/base_policy_rule.py`** | Abstract Contract | Abstract base class `BasePolicyRule` defining rule interfaces. |
| **`rules/read_only_auto_approval_rule.py`** | Policy Rule | Auto-approves safe read-only and inspection actions. |
| **`rules/production_protection_rule.py`** | Policy Rule | Enforces human approval for production mutations and blocks destructive commands. |
| **`rules/critical_infrastructure_rule.py`**| Policy Rule | Enforces specialized Critical/Security approvals for database and firewall modifications. |
| **`rules/container_k8s_policy_rule.py`**| Policy Rule | Enforces human approval for Docker and Kubernetes actions. |
| **`README.md`** | Documentation | Onboarding documentation for software engineers. |

---

## 📥 5. Inputs & Outputs

- **Input**: `RecommendationReport` (produced by Phase 5 `domain/recommendation/models.py`).
- **Output**: `PolicyDecision` containing `overall_decision`, `approved_actions`, `rejected_actions`, `approval_requests`, `policy_violations`, and `risk_classification`.
