# 🛡️ Autonomous AI SRE Platform for Autonomous Operations

> **A Production-Grade Autonomous Site Reliability Engineering (SRE) Platform for Capability Discovery, Incident Investigation, Multi-Command Execution, Data Correlation, AI Root Cause Analysis, Operational Guidance, Policy Governance, and Grounded Copilot Conversations.**

---

## 📌 1. Executive Overview

The **Autonomous AI SRE Platform** is an enterprise-grade autonomous incident investigation engine designed to emulate the reasoning, host probing, and troubleshooting methodology of a Senior Site Reliability Engineer (SRE).

When a natural language query (e.g., *"Why is my server slow and unresponsive?"*) is submitted, the platform executes a deterministic, multi-stage workflow starting with pre-planning host capability discovery, executing a 6-phase diagnostic pipeline, synthesizing executive answers, and enabling an evidence-grounded Copilot workspace for follow-up questions:

```text
User Natural Language Question
              │
              ▼
┌──────────────────────────────────────────────┐
│  Phase 0: Pre-Planning Capability Discovery  │ ➔ Single read-only SSH probe for OS, distro & tools
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Phase 1: Investigation Planning Engine      │ ➔ Builds capability-filtered InvestigationPlan
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Phase 2: Multi-Command Execution Engine     │ ➔ Executes steps over SSH concurrently
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Phase 3: Data Correlation Engine            │ ➔ Synthesizes findings & evidence (No AI)
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Phase 4: AI Root Cause Analysis Engine      │ ➔ AI reasons over structured findings only
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Phase 5: Operational Recommendation Engine  │ ➔ Formulates guidance & rollback plans
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Phase 6: Policy Engine & Approval Framework │ ➔ Evaluates safety & approval permission matrix
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Synthesis Layer: Executive Summary Service  │ ➔ Generates direct executive response
└─────────────────────┬────────────────────────┘
                      │
                      ▼
          Unified InvestigationReport
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  Interactive Layer: AI SRE Copilot Workspace │ ➔ Evidence-grounded follow-up Q&A (No re-exec)
└──────────────────────────────────────────────┘
```

---

## 🏗️ 2. Clean Architecture & Layering

The codebase strictly adheres to **Clean Architecture**, **Domain-Driven Design (DDD)**, and **SOLID** principles. Core business logic is isolated in the `domain/` layer and has **zero dependencies** on external frameworks, SSH libraries, database drivers, or AI vendor SDKs.

```mermaid
graph TD
    subgraph Presentation Layer
        UI[Streamlit Web Dashboard]
        CLI[Terminal CLI App]
    end

    subgraph Application Layer
        WF[InvestigationWorkflow]
        P0_APP[CapabilityDiscoveryService]
        P1_APP[Planner App Service]
        P2_APP[ExecutionService]
        P3_APP[CorrelationService]
        P4_APP[RCAService]
        P5_APP[RecommendationService]
        P6_APP[PolicyService]
        SUM_APP[ExecutiveSummaryService]
        COP_CTX_APP[InvestigationContextService]
        COP_CONV_APP[ConversationService]
    end

    subgraph Domain Layer
        REPORT[InvestigationReport Model]
        P0_DOM[ServerCapabilities & CapabilityPolicy]
        P1_DOM[Plan Models & Rules]
        P2_DOM[Step & Execution Models]
        P3_DOM[Findings & Correlation Rules]
        P4_DOM[RCA Models & AI Gateway Interface]
        P5_DOM[Recommendation Models & AI Gateway Interface]
        P6_DOM[Policy Rules & Decision Models]
        COP_DOM[InvestigationContext & Conversation Models]
    end

    subgraph Infrastructure Layer
        SSH_INFRA[Paramiko SSH Client]
        CAP_INFRA[CapabilityDiscoveryEngine]
        DB_INFRA[PostgreSQL Audit Repository]
        LLM_INFRA[Gemini RCA & Recommendation Providers]
        REG_INFRA[Linux Command & Parser Registries]
        COP_INFRA[InMemoryInvestigationContextRepository]
    end

    UI --> WF
    CLI --> WF
    UI --> COP_CONV_APP
    UI --> COP_CTX_APP

    WF --> P0_APP
    WF --> P1_APP
    WF --> P2_APP
    WF --> P3_APP
    WF --> P4_APP
    WF --> P5_APP
    WF --> P6_APP
    WF --> SUM_APP

    P0_APP --> P0_DOM
    P1_APP --> P1_DOM
    P2_APP --> P2_DOM
    P3_APP --> P3_DOM
    P4_APP --> P4_DOM
    P5_APP --> P5_DOM
    P6_APP --> P6_DOM
    COP_CTX_APP --> COP_DOM
    COP_CONV_APP --> COP_DOM

    P0_APP -.-> CAP_INFRA
    CAP_INFRA -.-> SSH_INFRA
    P2_APP -.-> SSH_INFRA
    P2_APP -.-> DB_INFRA
    P2_APP -.-> REG_INFRA
    P4_APP -.-> LLM_INFRA
    P5_APP -.-> LLM_INFRA
    COP_CTX_APP -.-> COP_INFRA
    COP_CONV_APP -.-> COP_INFRA
```

---

## 🔄 3. End-to-End Execution Sequence Flow

The following sequence diagram demonstrates the flow of data through the platform for an incident investigation query, starting from host capability probing through to interactive follow-up via the AI SRE Copilot:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Presentation as Presentation Layer (Streamlit / CLI)
    participant Workflow as InvestigationWorkflow (Application)
    participant P0 as Phase 0: Capability Discovery
    participant P1 as Phase 1: Planner
    participant P2 as Phase 2: Execution Engine
    participant SSH as Infrastructure: Paramiko SSH
    participant DB as Infrastructure: PostgreSQL Audit DB
    participant P3 as Phase 3: Correlation Engine
    participant P4 as Phase 4: AI RCA Engine
    participant LLM as Infrastructure: Gemini LLM Gateway
    participant P5 as Phase 5: Recommendation Engine
    participant P6 as Phase 6: Policy Engine
    participant Copilot as Copilot: ConversationService
    
    User->>Presentation: "Why is my server slow?"
    Presentation->>Workflow: execute_investigation(query)
    
    rect rgb(235, 245, 255)
        note over Workflow,P0: Phase 0: Pre-Planning Capability Discovery
        Workflow->>P0: discover()
        P0->>SSH: execute_command(single read-only probe)
        SSH-->>P0: stdout (OS, distro, kernel, binary check)
        P0-->>Workflow: ServerCapabilities (Installed tools & domains)
    end

    rect rgb(240, 248, 255)
        note over Workflow,P1: Phase 1: Investigation Planning
        Workflow->>P1: create_plan(query, capabilities)
        P1->>P1: Apply CapabilityAwarePlanPolicy (filter missing tools)
        P1-->>Workflow: InvestigationPlan (Capability-filtered diagnostic steps)
    end
    
    rect rgb(255, 245, 238)
        note over Workflow,P2: Phase 2: Multi-Command Execution
        Workflow->>P2: execute_plan(plan)
        par Concurrent Step Execution
            P2->>SSH: execute_command(cat /proc/loadavg)
            P2->>SSH: execute_command(free -m)
            P2->>SSH: execute_command(df -h)
        end
        P2->>DB: save_audit_log(stdout, stderr)
        P2-->>Workflow: InvestigationExecutionResult
    end
    
    rect rgb(240, 255, 240)
        note over Workflow,P3: Phase 3: Data Correlation
        Workflow->>P3: correlate(execution_result)
        P3->>P3: Evaluate CPUSaturationRule, MemoryPressureRule, DiskCapacityRule...
        P3-->>Workflow: CorrelationResult (Structured Findings & Empirical Evidence)
    end
    
    rect rgb(255, 240, 245)
        note over Workflow,P4: Phase 4: AI Root Cause Analysis
        Workflow->>P4: analyze_root_cause(correlation_result)
        P4->>LLM: generate_content(Structured Findings Prompt)
        LLM-->>P4: JSON (Primary Cause, Hypotheses, Reasoning Trace)
        P4-->>Workflow: RootCauseAnalysis
    end

    rect rgb(250, 240, 230)
        note over Workflow,P5: Phase 5: Operational Recommendation
        Workflow->>P5: generate_report(rca_output)
        P5->>LLM: generate_content(RCA Guidance Prompt)
        LLM-->>P5: JSON (Action Items, Validation Steps, Rollback Plan)
        P5-->>Workflow: RecommendationReport
    end

    rect rgb(245, 245, 255)
        note over Workflow,P6: Phase 6: Policy & Governance
        Workflow->>P6: evaluate_report(recommendation_report)
        P6->>P6: Evaluate ProductionProtectionRule, ReadOnlyAutoApprovalRule...
        P6-->>Workflow: PolicyDecision (Approved Actions, Prohibited Actions)
    end
    
    Workflow-->>Presentation: Unified InvestigationReport
    Presentation-->>User: Render Interactive Multi-Tab Report & Dashboard

    rect rgb(240, 240, 250)
        note over Presentation,Copilot: Interactive Layer: AI SRE Copilot Workspace
        User->>Presentation: "How do I fix the high memory issue?"
        Presentation->>Copilot: answer_follow_up(investigation_id, question)
        Copilot->>Copilot: Query saved InvestigationContext & findings (No SSH execution)
        Copilot-->>Presentation: ConversationMessage (Grounded Answer + Evidence Citations)
        Presentation-->>User: Render grounded answer with evidence citation drawer
    end
```

---

## 📑 4. Phase-by-Phase Architectural Breakdown

### **Phase 0 — Pre-Planning Capability Discovery Engine (`domain/capability/`, `application/capability/`, & `infrastructure/capabilities/`)**
- **Purpose**: Performs a lightweight, read-only host inspection over SSH *before* generating an investigation plan. This guarantees that diagnostic plans only target installed, supported software and binaries.
- **Components**:
  - `CapabilityDiscoveryEngine`: Executes a single composite read-only shell probe over SSH checking OS release (`/etc/os-release`), kernel version (`uname -r`), and binary availability (`docker`, `kubectl`, `psql`, `nginx`, `systemctl`, `python3`, `lvs`, etc.).
  - `CapabilityDiscoveryService`: Application service wrapper exposing the host discovery interface.
  - `CapabilityAwarePlanPolicy`: Domain policy filtering diagnostic steps based on detected capabilities. For instance, if `kubectl` is absent, Kubernetes diagnostic steps are skipped cleanly with an informative notice.
- **Investigation Domains Discovered**: `CPU`, `MEMORY`, `DISK`, `NETWORK`, `SERVICES`, `CONTAINERS`, `KUBERNETES`, `POSTGRESQL`, `MYSQL`, `REDIS`.
- **Output**: `ServerCapabilities` domain model containing operating system metadata, installed technology lists, supported investigation domains, and discovery metrics.

---

### **Phase 1 — Investigation Planning Engine (`domain/investigation/` & `application/investigation/`)**
- **Purpose**: Translates natural language user queries into a capability-aware `InvestigationPlan` containing diagnostic steps without connecting to any remote server or executing commands.
- **Components**:
  - `InvestigationPlanner`: Application entry point orchestrating rule engine, template matching, and capability filtering.
  - `RuleEngine`: Pattern matcher mapping query keywords to diagnostic templates.
  - `TemplateRegistry`: Standardized diagnostic step templates (`slow_server`, `high_memory`, `high_cpu`, `disk_space`, `network_connectivity`).
  - `StrategyEvaluator`: Assigns `SEQUENTIAL` vs `PARALLEL` execution strategies and duration estimates.
- **Output**: Capability-filtered `InvestigationPlan` domain model.

---

### **Phase 2 — Multi-Command Execution Engine (`domain/execution/` & `application/execution/`)**
- **Purpose**: Executes diagnostic steps in an `InvestigationPlan` across remote SSH worker threads concurrently and logs all commands to audit persistence.
- **Components**:
  - `ExecutionService`: Main orchestrator choosing between `SequentialRunner` and `ParallelRunner`.
  - `ParallelRunner`: Concurrent worker pool using `ThreadPoolExecutor` with per-step timeout budgets.
  - `StepExecutor`: Executes single steps, invokes SSH, saves PostgreSQL audit logs, and parses terminal stdout into JSON.
- **Output**: `InvestigationExecutionResult` containing `StepExecutionResult` list and `ExecutionMetrics`.

---

### **Phase 3 — Data Correlation Engine (`domain/correlation/` & `application/correlation/`)**
- **Purpose**: Evaluates relationships across independent metric observations to produce structured **Operational Findings** backed by empirical **Evidence**. Operates purely on rule evaluators without AI calls.
- **Rule Evaluators**:
  - `CPUSaturationRule`: Correlates system load averages with process CPU utilization.
  - `MemoryPressureRule`: Correlates RAM utilization with active swap space memory thrashing.
  - `DiskCapacityRule`: Evaluates mounted filesystem space utilization against capacity thresholds.
  - `NetworkSocketsRule`: Evaluates open listening sockets and network service activity.
  - `ServiceFailureRule`: Detects systemd units in failed state.
  - `ContainerHealthRule`: Detects crashed Docker containers or Kubernetes pod failures.
- **Output**: `CorrelationResult` containing `Finding` list and empirical `Evidence` containers.

---

### **Phase 4 — AI Root Cause Analysis Engine (`domain/rca/`, `application/rca/`, & `infrastructure/llm/`)**
- **Purpose**: AI reasoning engine determining the authoritative primary root cause.
- **Zero-Hallucination Guardrail**: **The AI NEVER receives raw terminal output, raw SSH stdout, or unparsed logs.** It reasons *exclusively* over structured `CorrelationResult` findings.
- **AI Gateway Abstraction**: Decoupled via `LLMProviderInterface`. `GeminiRCAProvider` implements the interface with deterministic fallback logic.
- **Output**: `RootCauseAnalysis` domain model containing primary root cause, confidence score, primary hypothesis, alternative hypotheses, and 5-step reasoning trace.

---

### **Phase 5 — Operational Recommendation Engine (`domain/recommendation/`, `application/recommendation/`, & `infrastructure/llm/`)**
- **Purpose**: Converts Root Cause Analysis into actionable operational guidance, validation checks, and rollback plans.
- **Safety Principle**: Recommendations are advisory guidance only and **NEVER execute actions directly**.
- **AI Gateway Abstraction**: Decoupled via `RecommendationProviderInterface`. `GeminiRecommendationProvider` implements the provider interface.
- **Output**: `RecommendationReport` domain model containing prioritized action items (`Recommendation`), `ValidationStep` entries, and `RollbackPlan`.

---

### **Phase 6 — Policy Engine & Approval Framework (`domain/policy/` & `application/policy/`)**
- **Purpose**: The safety perimeter of the AI SRE Platform. Evaluates recommended actions against security and operational policies before any action can be automated.
- **Approval Permission Matrix**:
  - `AUTO_APPROVED` / `ALLOWED_AUTOMATED`: Read-only inspection and safe diagnostic queries. Authorized Role: `Automated SRE System`.
  - `HUMAN_APPROVAL_REQUIRED` / `ALLOWED_MANUAL_ONLY`: Production service restarts, process termination, or scaling. Authorized Role: `Senior SRE`.
  - `CRITICAL_APPROVAL_REQUIRED` / `ALLOWED_MANUAL_ONLY`: High-impact database changes. Authorized Role: `Principal SRE`.
  - `SECURITY_APPROVAL_REQUIRED` / `ALLOWED_MANUAL_ONLY`: Firewall or security policy modifications. Authorized Role: `Security Admin`.
  - `PROHIBITED` / `BLOCKED`: Destructive operations (e.g. `rm -rf /`). Authorized Role: `Blocked`.
- **Policy Rules**: `ReadOnlyAutoApprovalRule`, `ProductionProtectionRule`, `CriticalInfrastructureRule`, `ContainerK8sPolicyRule`.
- **Output**: `PolicyDecision` domain model containing approved actions, rejected actions, and policy violations.

---

### **Synthesis Layer — Executive Summary Service (`application/summary/`)**
- **Purpose**: Synthesizes the outputs of Phases 1 through 6 into a concise, human-readable executive investigation summary that directly answers the user's initial query at the top of the interface.
- **Output**: `ExecutiveInvestigationSummary` domain model.

---

### **Interactive Layer — AI SRE Copilot Workspace (`domain/copilot/`, `application/copilot/`, & `infrastructure/persistence/`)**
- **Purpose**: Enables interactive, multi-turn follow-up Q&A grounded exclusively in the saved artifacts of a completed investigation.
- **Safety Perimeter**: **Strictly read-only with zero execution capability.** It cannot trigger SSH commands, re-run pipelines, or perform server mutations.
- **Key Components**:
  - `InvestigationContextService`: Captures completed `InvestigationReport` artifacts and builds contextual metadata and suggested follow-up questions.
  - `ConversationService`: Processes follow-up questions, searching saved correlation findings, root cause reasoning, and recommendations to generate responses backed by `EvidenceCitation`s.
  - `InMemoryInvestigationContextRepository`: Session-scoped, process-local repository storing investigation context and conversation histories.
- **Output**: Grounded `ConversationMessage` objects containing exact citations to metric names, observed values, thresholds, and source commands.

---

## 📁 5. Complete Directory Tree

```text
e:\paramiko\
├── app.py                                  # Legacy backend entrypoint
├── run.py                                  # CLI entrypoint
├── frontend.py                             # Streamlit web UI entrypoint
├── commands.py                             # Legacy whitelisted command registry data
├── parsers.py                              # Legacy regular expression output parsers
├── ssh_client.py                           # Legacy Paramiko connection manager
├── database.py                             # Legacy PostgreSQL log helper
├── llm.py                                  # Legacy Gemini helper
│
├── application/                            # Use Case Orchestrators & Workflows
│   ├── workflow/                           # InvestigationWorkflow (Phase 0 probe -> P1-P6 pipeline -> Executive summary)
│   ├── capability/                         # CapabilityDiscoveryService (Phase 0 host capability probing)
│   ├── investigation/                      # Phase 1 planning app services
│   ├── execution/                          # Phase 2 multi-command execution app services
│   ├── correlation/                        # Phase 3 correlation app services
│   ├── rca/                                # Phase 4 AI RCA app services
│   ├── recommendation/                     # Phase 5 operational recommendation app services
│   ├── policy/                             # Phase 6 policy engine app services
│   ├── summary/                            # ExecutiveSummaryService synthesis
│   └── copilot/                            # AI SRE Copilot services (ConversationService, InvestigationContextService)
│
├── domain/                                 # Pure Business Logic, Models, Rules & Interfaces
│   ├── report/                             # Unified InvestigationReport model
│   ├── capability/                         # ServerCapabilities models & CapabilityAwarePlanPolicy
│   ├── investigation/                      # Phase 1 models, rules & templates
│   ├── execution/                          # Phase 2 models & execution contracts
│   ├── correlation/                        # Phase 3 findings & domain rules
│   ├── rca/                                # Phase 4 RCA models & AI Gateway interface
│   ├── recommendation/                     # Phase 5 guidance models & AI Gateway interface
│   ├── policy/                             # Phase 6 policy decision models & rules
│   └── copilot/                            # Copilot domain models (InvestigationContext, ConversationMessage, EvidenceCitation)
│
├── infrastructure/                         # External Integrations & Concrete Implementations
│   ├── capabilities/                       # CapabilityDiscoveryEngine (SSH capability discovery probe)
│   ├── ssh/                                # Paramiko SSH Client (ISSHClient interface)
│   ├── llm/                                # Gemini RCA & Recommendation Providers
│   ├── registry/                           # Linux Command & Parser Registries
│   └── persistence/                        # Audit DB & Copilot Repositories (PostgresAuditRepository, InMemoryInvestigationContextRepository)
│
├── presentation/                           # Presentation Layer (UI & CLI)
│   ├── streamlit/                          # Streamlit Web Dashboard with Copilot workspace & Capability drawer
│   └── cli/                                # Terminal CLI Application
│
└── shared/                                 # Cross-Cutting Platform Utilities
    ├── config/                             # Central Settings (PlatformSettings)
    ├── logging/                            # Structured Logger (get_logger)
    └── exceptions/                         # Global Platform Exceptions
```

---

## 🛠️ 6. How to Extend the Platform

### **1. How to Add a New Capability Probe**
1. Open `infrastructure/capabilities/capability_discovery_engine.py`.
2. Add a `TechnologyDefinition` to `_TECHNOLOGIES` specifying name, executable, and category.
3. Map the tech to an `InvestigationDomain` in `_build_investigation_capabilities()`.

### **2. How to Add a New LLM Provider (e.g. OpenAI or Claude)**
1. Create a new provider adapter in `infrastructure/llm/` (e.g., `openai_provider.py`).
2. Implement `LLMProviderInterface` from `domain/rca/llm_interface.py`.
3. Pass your new provider into `RCAService(provider=OpenAIRCAProvider())` via Dependency Injection.

### **3. How to Add a New Correlation Rule**
1. Create a new rule file in `domain/correlation/rules/` (e.g., `kubernetes_rules.py`).
2. Inherit from `BaseCorrelationRule` and implement `evaluate(step_results) -> List[Finding]`.
3. Register your rule in `application/correlation/rule_registry.py`.

### **4. How to Add a New Policy Rule**
1. Create a new policy rule file in `domain/policy/rules/` (e.g., `compliance_rule.py`).
2. Inherit from `BasePolicyRule` and implement `evaluate_action(recommendation)`.
3. Register your rule in `application/policy/policy_registry.py`.

---

## 🚀 7. Quickstart Guide

### **Environment Configuration (`.env`)**
Create a `.env` file in the project root:
```env
SSH_HOST=testserv.ortusolis.in
SSH_PORT=22
SSH_USERNAME=your_username
SSH_PASSWORD=your_password

DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_db_password

GEMINI_API_KEY=your_gemini_api_key
```

### **Run Web Dashboard (Streamlit)**
```powershell
.\myvenv\Scripts\streamlit.exe run frontend.py
```

### **Run Terminal CLI**
```powershell
.\myvenv\Scripts\python.exe run.py "Why is my server slow and unresponsive?"
```

---

## 🧪 8. Verification & Testing

To run the complete unit test suite (including Capability Discovery and Copilot tests):
```powershell
.\myvenv\Scripts\python.exe -m unittest discover -s tests
```
