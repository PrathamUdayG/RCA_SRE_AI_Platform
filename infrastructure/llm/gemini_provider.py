"""
Purpose
-------
Gemini implementation of the LLMProviderInterface for AI Root Cause Analysis.

Responsibilities
----------------
- Format structured CorrelationResult findings into SRE prompts.
- Call Gemini API to generate structured Root Cause Analysis payloads.
- Parse JSON markdown output into validated RootCauseAnalysis domain models.
- Provide deterministic fallback if API keys or network calls are unavailable.

Does NOT
---------
- Accept raw unparsed terminal stdout.
- Execute SSH commands.
"""

from datetime import datetime
import json
import os
import re
import time
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

from domain.correlation.models import CorrelationResult
from domain.rca.exceptions import LLMProviderError
from domain.rca.llm_interface import LLMProviderInterface
from domain.rca.models import (
    AffectedComponent,
    AnalysisMetadata,
    Hypothesis,
    ReasoningTrace,
    RootCauseAnalysis,
    SupportingEvidence,
)
from domain.recommendation.models import RecommendationReport

load_dotenv()



class GeminiRCAProvider(LLMProviderInterface):
    """
    Concrete Gemini AI Provider implementing LLMProviderInterface.
    """

    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model_name = model_name
        self._client = genai.Client(api_key=self._api_key) if self._api_key else None

    @property
    def provider_name(self) -> str:
        return "Gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def analyze_correlation(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        """
        Synthesizes correlated operational findings into a structured RootCauseAnalysis object using Gemini.
        """
        start_time = time.time()
        executed_at = datetime.utcnow()

        # Build prompt payload from structured findings
        prompt = self._build_prompt(correlation_result)

        if not self._client:
            # Deterministic fallback synthesis if no API key is available
            return self._fallback_synthesis(correlation_result, start_time, executed_at)

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )

            response_text = response.text.strip() if response and response.text else ""
            clean_json_str = self._clean_json(response_text)
            data = json.loads(clean_json_str)

            duration = round(time.time() - start_time, 3)
            return self._parse_rca_model(data, correlation_result, duration, executed_at)

        except Exception as exc:
            # Fallback on LLM parsing error
            return self._fallback_synthesis(correlation_result, start_time, executed_at, error_reason=str(exc))

    def _build_prompt(self, correlation_result: CorrelationResult) -> str:
        """Builds a strict JSON system prompt from structured correlation findings."""
        findings_summary = []
        for f in correlation_result.findings:
            ev_list = [
                {"metric": ev.metric_name, "value": str(ev.observed_value), "threshold": str(ev.threshold)}
                for ev in f.evidences
            ]
            findings_summary.append({
                "title": f.title,
                "category": f.category.value,
                "severity": f.severity.value,
                "summary": f.summary,
                "evidences": ev_list,
                "affected_resources": f.affected_resources,
            })

        prompt_str = f"""
You are a Principal Site Reliability Engineer (SRE) performing an autonomous incident investigation.

User Question: "{correlation_result.user_question}"

Structured Operational Findings:
{json.dumps(findings_summary, indent=2)}

Instructions:
1. Analyze the structured findings and empirical evidences above.
2. Determine the Primary Root Cause.
3. Formulate the Primary Hypothesis and any Alternative Hypotheses.
4. Output a step-by-step Reasoning Trace.
5. Identify Affected Components.
6. Respond ONLY in valid JSON format matching this exact schema:

{{
  "primary_root_cause": "Authoritative root cause statement",
  "overall_confidence": 0.95,
  "summary": "Executive incident diagnosis summary",
  "primary_hypothesis": {{
    "title": "Primary hypothesis title",
    "description": "Detailed explanation of mechanism",
    "likelihood_score": 0.95,
    "supporting_evidences": [
      {{
        "metric_name": "metric_name",
        "observed_value": "observed_value",
        "finding_title": "finding_title",
        "relevance_explanation": "relevance_explanation"
      }}
    ]
  }},
  "alternative_hypotheses": [],
  "reasoning_trace": [
    {{
      "step_number": 1,
      "observation": "Observed symptom",
      "deduction": "Logical deduction"
    }}
  ],
  "affected_components": [
    {{
      "component_type": "MEMORY",
      "name": "RAM",
      "impact_level": "HIGH"
    }}
  ]
}}
"""
        return prompt_str

    def _clean_json(self, text: str) -> str:
        """Strips markdown code fences from LLM output."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        return cleaned.strip()

    def _parse_rca_model(
        self,
        data: Dict[str, Any],
        corr: CorrelationResult,
        duration: float,
        executed_at: datetime
    ) -> RootCauseAnalysis:
        """Transforms parsed dictionary into RootCauseAnalysis domain object."""
        prim_hyp_data = data.get("primary_hypothesis", {})
        supp_evidences = [
            SupportingEvidence(
                metric_name=ev.get("metric_name", "unknown"),
                observed_value=ev.get("observed_value", "unknown"),
                finding_title=ev.get("finding_title", "finding"),
                relevance_explanation=ev.get("relevance_explanation", "Supports hypothesis"),
            )
            for ev in prim_hyp_data.get("supporting_evidences", [])
        ]

        primary_hypothesis = Hypothesis(
            title=prim_hyp_data.get("title", "Primary Operational Finding"),
            description=prim_hyp_data.get("description", "Analyzed from correlated findings."),
            likelihood_score=float(prim_hyp_data.get("likelihood_score", 0.9)),
            is_primary=True,
            supporting_evidences=supp_evidences,
        )

        alt_hypotheses = []
        for alt in data.get("alternative_hypotheses", []):
            alt_hypotheses.append(
                Hypothesis(
                    title=alt.get("title", "Alternative Hypothesis"),
                    description=alt.get("description", ""),
                    likelihood_score=float(alt.get("likelihood_score", 0.3)),
                    is_primary=False,
                )
            )

        reasoning_traces = [
            ReasoningTrace(
                step_number=rt.get("step_number", idx + 1),
                observation=rt.get("observation", ""),
                deduction=rt.get("deduction", ""),
            )
            for idx, rt in enumerate(data.get("reasoning_trace", []))
        ]

        affected_comps = [
            AffectedComponent(
                component_type=ac.get("component_type", "SYSTEM"),
                name=ac.get("name", "Host"),
                impact_level=ac.get("impact_level", "MEDIUM"),
            )
            for ac in data.get("affected_components", [])
        ]

        metadata = AnalysisMetadata(
            provider_used=self.provider_name,
            model_name=self.model_name,
            analysis_duration_seconds=duration,
            total_findings_analyzed=len(corr.findings),
        )

        return RootCauseAnalysis(
            correlation_id=corr.correlation_id,
            investigation_id=corr.investigation_id,
            user_question=corr.user_question,
            primary_root_cause=data.get("primary_root_cause", "No primary root cause identified."),
            overall_confidence=float(data.get("overall_confidence", 0.9)),
            summary=data.get("summary", "Analysis completed."),
            primary_hypothesis=primary_hypothesis,
            alternative_hypotheses=alt_hypotheses,
            reasoning_trace=reasoning_traces,
            affected_components=affected_comps,
            metadata=metadata,
            created_at=executed_at,
        )

    def _fallback_synthesis(
        self,
        corr: CorrelationResult,
        start_time: float,
        executed_at: datetime,
        error_reason: str = None
    ) -> RootCauseAnalysis:
        """Deterministic rule-based fallback when Gemini API is unconfigured or unreachable."""
        duration = round(time.time() - start_time, 3)

        has_execution_failures = any("Execution Failed" in f.title or "Failure" in f.title for f in corr.findings)

        if not corr.findings:
            primary_rc = "Investigation Inconclusive — insufficient evidence collected from host."
            summary = "No diagnostic metric findings could be extracted. Unable to verify system health."
            confidence = 0.1
            primary_hyp = Hypothesis(
                title="Investigation Inconclusive",
                description="No operational evidence was retrieved from server diagnostics.",
                likelihood_score=0.1,
                is_primary=True,
            )
            reasoning = [
                ReasoningTrace(step_number=1, observation="Zero correlated findings retrieved.", deduction="Cannot establish root cause without empirical evidence.")
            ]
            affected = [AffectedComponent(component_type="SYSTEM", name="Server Host", impact_level="HIGH")]
        elif has_execution_failures and len(corr.findings) == sum(1 for f in corr.findings if "Execution Failed" in f.title or "Failure" in f.title):
            primary_rc = "Investigation Inconclusive — Diagnostic SSH command execution failed."
            summary = "Remote diagnostic commands failed to execute. Infrastructure telemetry could not be gathered."
            confidence = 0.1
            primary_hyp = Hypothesis(
                title="Diagnostic Execution Failure",
                description="Commands executed over SSH failed or returned no output.",
                likelihood_score=0.1,
                is_primary=True,
            )
            reasoning = [
                ReasoningTrace(step_number=idx + 1, observation=f.title, deduction=f.summary)
                for idx, f in enumerate(corr.findings)
            ]
            affected = [AffectedComponent(component_type="SYSTEM", name="SSH Connectivity", impact_level="CRITICAL")]
        else:
            top_finding = max(corr.findings, key=lambda f: f.confidence_score)
            primary_rc = f"Primary cause associated with {top_finding.title}: {top_finding.summary}"
            summary = f"Synthesized diagnosis: {top_finding.title} ({top_finding.summary}) based on {len(corr.findings)} correlated finding(s)."
            confidence = top_finding.confidence_score

            supp_evs = [
                SupportingEvidence(
                    metric_name=ev.metric_name,
                    observed_value=ev.observed_value,
                    finding_title=top_finding.title,
                    relevance_explanation="Direct empirical metric violation.",
                )
                for ev in top_finding.evidences
            ]

            primary_hyp = Hypothesis(
                title=top_finding.title,
                description=top_finding.summary,
                likelihood_score=confidence,
                is_primary=True,
                supporting_evidences=supp_evs,
            )

            reasoning = [
                ReasoningTrace(
                    step_number=idx + 1,
                    observation=f.title,
                    deduction=f.summary,
                )
                for idx, f in enumerate(corr.findings)
            ]

            affected = [
                AffectedComponent(component_type=f.category.value, name=res, impact_level=f.severity.value)
                for f in corr.findings
                for res in f.affected_resources
            ]

        metadata = AnalysisMetadata(
            provider_used="Gemini (Fallback Engine)" if error_reason else "Deterministic Synthesizer",
            model_name=self.model_name,
            analysis_duration_seconds=duration,
            total_findings_analyzed=len(corr.findings),
        )

        return RootCauseAnalysis(
            correlation_id=corr.correlation_id,
            investigation_id=corr.investigation_id,
            user_question=corr.user_question,
            primary_root_cause=primary_rc,
            overall_confidence=confidence,
            summary=summary,
            primary_hypothesis=primary_hyp,
            alternative_hypotheses=[],
            reasoning_trace=reasoning,
            affected_components=affected,
            metadata=metadata,
            created_at=executed_at,
        )

    def generate_executive_summary(
        self,
        user_question: str,
        correlation_result: CorrelationResult = None,
        rca: RootCauseAnalysis = None,
        recommendation: RecommendationReport = None,
    ) -> str:
        """
        Synthesizes executive direct answer narrative to user question using Gemini.
        """
        if not self._client:
            return self._fallback_executive_summary(user_question, correlation_result, rca, recommendation)

        prompt = f"""
You are a Principal Site Reliability Engineer (SRE). Provide a concise, professional 1-2 paragraph executive response directly answering the user's natural language question: "{user_question}".

Investigation Details:
- Primary Root Cause: {rca.primary_root_cause if rca else 'Inconclusive'}
- Confidence: {rca.overall_confidence if rca else 0.0}
- Correlated Findings: {[f.title for f in correlation_result.findings] if correlation_result else []}
- Operational Recommendation: {recommendation.executive_summary if recommendation else 'N/A'}

Instructions:
- Directly answer the user's question.
- Synthesize investigation objective, empirical findings, confidence, and recommended remediation.
- Return plain narrative text without markdown code fences or JSON formatting.
"""
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
            return self._fallback_executive_summary(user_question, correlation_result, rca, recommendation)
        except Exception:
            return self._fallback_executive_summary(user_question, correlation_result, rca, recommendation)

    def _fallback_executive_summary(
        self,
        user_question: str,
        corr: CorrelationResult = None,
        rca: RootCauseAnalysis = None,
        rec: RecommendationReport = None,
    ) -> str:
        findings_count = len(corr.findings) if corr and corr.findings else 0
        primary_rc = rca.primary_root_cause if rca else "Investigation Inconclusive"
        conf_pct = f"{round(rca.overall_confidence * 100, 1)}%" if rca else "N/A"
        top_rec = rec.executive_summary if rec else "Perform manual server diagnostics."

        if not corr or not corr.findings:
            return (
                f"The investigation into '{user_question}' completed, but zero anomalous metrics were detected. "
                f"All evaluated system indicators appear within normal operating thresholds. "
                f"Recommended Action: {top_rec}"
            )

        top_finding = corr.findings[0]
        ev_details = [f"{ev.metric_name} is currently at {ev.observed_value} (threshold: {ev.threshold})" for ev in top_finding.evidences]
        ev_str = "; ".join(ev_details) if ev_details else top_finding.summary

        return (
            f"The investigation into '{user_question}' completed with {conf_pct} confidence based on {findings_count} correlated operational finding(s). "
            f"Primary Cause: {primary_rc}. Key Evidence: {ev_str}. "
            f"Recommended Operational Action: {top_rec}"
        )
