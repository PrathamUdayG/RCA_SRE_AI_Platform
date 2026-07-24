"""
Purpose
-------
Centralized LLM Provider Manager for the AI SRE Platform.
Serves as the authoritative single source of truth for provider registration, active provider
selection, multi-provider fallback ordering, health probing, and structured LLM invocation logging.

Responsibilities
----------------
- Register and maintain all platform LLM providers (Gemini, Hugging Face, OpenRouter, Groq, Fallback Engine).
- Probe provider connectivity and determine the true active operational LLM provider.
- Orchestrate automatic fallback execution when primary AI providers encounter network timeouts, API errors, or invalid responses.
- Enforce mandatory structured logging on EVERY LLM invocation:
  - Provider selected
  - Model name
  - Execution latency (seconds/ms)
  - Prompt payload size
  - Completion response size
  - Success/Failure status
  - Fallback indicator
  - Error exception details (if any)
- Ensure Domain, Application, and Presentation layers observe 100% consistent provider health and active model metadata.

Does NOT
--------
- Modify low-level Linux parsers or SSH transport.
"""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional, Tuple

from domain.correlation.models import CorrelationResult
from domain.health.models import ComponentHealthResult, ComponentStatus
from domain.llm import LLMProviderInterface
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.models import RecommendationReport
from shared.config import get_settings
from shared.logging import get_logger

from .gemini_provider import GeminiRCAProvider
from .huggingface_provider import HuggingFaceProvider

logger = get_logger("LLMProviderManager")


class DeterministicFallbackProvider(LLMProviderInterface):
    """
    Deterministic rule-based fallback LLM provider used when external LLM endpoints are unreachable or unconfigured.
    """

    def __init__(self, model_name: str = "Deterministic-Rule-Engine-v1"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "Deterministic Fallback Engine"

    @property
    def model_name(self) -> str:
        return self._model_name

    def health_check(self) -> ComponentHealthResult:
        return ComponentHealthResult(
            component_name="AI Provider (Fallback Engine)",
            category="AI",
            status=ComponentStatus.HEALTHY,
            details={
                "provider": self.provider_name,
                "model": self.model_name,
                "type": "Local Rule-Based Fallback",
                "api_connectivity": "Local Synthesizer",
            },
            checked_at=datetime.utcnow(),
            latency_ms=0.1,
        )

    def analyze_correlation(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        # Delegate to HuggingFace / Gemini fallback helper
        hf_prov = HuggingFaceProvider()
        return hf_prov._fallback_rca_synthesis(
            correlation_result,
            time.time(),
            datetime.utcnow(),
            error_reason="All primary LLM API endpoints unavailable — running deterministic fallback engine"
        )

    def generate_recommendations(self, rca: RootCauseAnalysis) -> RecommendationReport:
        hf_prov = HuggingFaceProvider()
        return hf_prov._fallback_recommendations_guidance(
            rca,
            time.time(),
            datetime.utcnow(),
            error_reason="All primary LLM API endpoints unavailable — running deterministic fallback engine"
        )

    def generate_executive_summary(
        self,
        user_question: str,
        correlation_result: Optional[CorrelationResult] = None,
        rca: Optional[RootCauseAnalysis] = None,
        recommendation: Optional[RecommendationReport] = None,
    ) -> str:
        # Deterministic rich natural language executive answer generator
        findings_count = len(correlation_result.findings) if correlation_result and correlation_result.findings else 0
        primary_rc = rca.primary_root_cause if rca else "Investigation Inconclusive"
        conf_pct = f"{round(rca.overall_confidence * 100, 1)}%" if rca else "N/A"
        top_rec = recommendation.executive_summary if recommendation else "Perform manual server diagnostics."

        if not correlation_result or not correlation_result.findings:
            return (
                f"The investigation into '{user_question}' completed, but zero anomalous metrics were detected. "
                f"All evaluated system indicators appear within normal operating thresholds. "
                f"Recommended Action: {top_rec}"
            )

        top_finding = correlation_result.findings[0]
        ev_details = []
        for ev in top_finding.evidences:
            ev_details.append(f"{ev.metric_name} is currently at {ev.observed_value} (threshold: {ev.threshold})")

        ev_str = "; ".join(ev_details) if ev_details else top_finding.summary

        return (
            f"The investigation into '{user_question}' completed with {conf_pct} confidence based on {findings_count} correlated operational finding(s). "
            f"Primary Cause: {primary_rc}. Key Evidence: {ev_str}. "
            f"Recommended Operational Action: {top_rec}"
        )


class LLMProviderManager(LLMProviderInterface):
    """
    Authoritative Centralized Manager for all Platform LLM capabilities.
    """

    _instance: Optional["LLMProviderManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMProviderManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._providers: List[LLMProviderInterface] = []
        self._fallback_provider = DeterministicFallbackProvider()
        self._initialize_providers()

    def _initialize_providers(self):
        """Initializes available providers based on platform configuration."""
        settings = get_settings()
        configured_provider = (settings.llm.provider or "huggingface").lower().strip()

        self._providers = []

        # Configure primary provider according to settings
        if configured_provider in ("huggingface", "hf", "qwen"):
            primary = HuggingFaceProvider()
            secondary = GeminiRCAProvider()
            self._providers = [primary, secondary]
        elif configured_provider == "gemini":
            primary = GeminiRCAProvider()
            secondary = HuggingFaceProvider()
            self._providers = [primary, secondary]
        else:
            self._providers = [HuggingFaceProvider(), GeminiRCAProvider()]

    def reload_providers(self):
        """Forces reload of provider registrations from environment/settings."""
        self._initialize_providers()

    @property
    def provider_name(self) -> str:
        active_provider, _ = self._resolve_active_provider()
        return active_provider.provider_name

    @property
    def model_name(self) -> str:
        active_provider, _ = self._resolve_active_provider()
        return active_provider.model_name

    def _resolve_active_provider(self) -> tuple[LLMProviderInterface, Dict[str, Any]]:
        """
        Probes registered providers and resolves the active operational provider.
        """
        settings = get_settings()
        configured_name = settings.llm.provider or "huggingface"
        provider_probe_details = {}

        for provider in self._providers:
            try:
                res = provider.health_check()
                provider_probe_details[provider.provider_name] = {
                    "status": res.status.value,
                    "model": provider.model_name,
                    "latency_ms": res.latency_ms,
                    "error": res.error_message,
                }
                if res.status == ComponentStatus.HEALTHY:
                    return provider, provider_probe_details
            except Exception as exc:
                provider_probe_details[provider.provider_name] = {
                    "status": ComponentStatus.UNHEALTHY.value,
                    "model": provider.model_name,
                    "error": str(exc),
                }

        # If all remote providers fail or are unconfigured, use deterministic fallback provider
        return self._fallback_provider, provider_probe_details

    def health_check(self) -> ComponentHealthResult:
        """
        Runs comprehensive health checks across all registered LLM providers and returns a unified ComponentHealthResult.
        """
        checked_at = datetime.utcnow()
        active_provider, probe_details = self._resolve_active_provider()

        is_fallback = isinstance(active_provider, DeterministicFallbackProvider)
        overall_status = ComponentStatus.DEGRADED if is_fallback else ComponentStatus.HEALTHY

        # If primary configured provider is healthy, overall AI status is HEALTHY
        settings = get_settings()
        configured_name = (settings.llm.provider or "huggingface").capitalize()

        details = {
            "configured_provider": configured_name,
            "active_provider": active_provider.provider_name,
            "active_model": active_provider.model_name,
            "using_fallback": is_fallback,
            "registered_providers": probe_details,
        }

        if is_fallback:
            error_msg = f"Primary configured provider ({configured_name}) is offline or unconfigured. Using deterministic fallback engine."
            rec_msg = "Verify LLM_API_KEY environment variable and API network connectivity."
        else:
            error_msg = None
            rec_msg = None

        logger.info(f"AI Provider Health Check: active={active_provider.provider_name}, model={active_provider.model_name}, status={overall_status.value}")

        return ComponentHealthResult(
            component_name="AI Provider",
            category="AI",
            status=overall_status,
            details=details,
            error_message=error_msg,
            recommendation=rec_msg,
            checked_at=checked_at,
        )

    def analyze_correlation(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        """
        Executes AI Root Cause Analysis with automatic multi-provider fallback and mandatory structured logging.
        """
        return self._execute_with_fallback(
            operation_name="analyze_correlation",
            method_caller=lambda p: p.analyze_correlation(correlation_result),
            fallback_caller=lambda: self._fallback_provider.analyze_correlation(correlation_result),
            prompt_summary=f"Question: '{correlation_result.user_question}', Findings: {len(correlation_result.findings)}",
        )

    def generate_recommendations(self, rca: RootCauseAnalysis) -> RecommendationReport:
        """
        Executes AI Recommendation Generation with automatic multi-provider fallback and mandatory structured logging.
        """
        return self._execute_with_fallback(
            operation_name="generate_recommendations",
            method_caller=lambda p: p.generate_recommendations(rca),
            fallback_caller=lambda: self._fallback_provider.generate_recommendations(rca),
            prompt_summary=f"RCA Primary: '{rca.primary_root_cause}', Confidence: {rca.overall_confidence}",
        )

    def generate_executive_summary(
        self,
        user_question: str,
        correlation_result: Optional[CorrelationResult] = None,
        rca: Optional[RootCauseAnalysis] = None,
        recommendation: Optional[RecommendationReport] = None,
    ) -> str:
        """
        Synthesizes executive direct answer narrative with automatic multi-provider fallback and mandatory structured logging.
        """
        return self._execute_with_fallback(
            operation_name="generate_executive_summary",
            method_caller=lambda p: p.generate_executive_summary(
                user_question=user_question,
                correlation_result=correlation_result,
                rca=rca,
                recommendation=recommendation,
            ),
            fallback_caller=lambda: self._fallback_provider.generate_executive_summary(
                user_question=user_question,
                correlation_result=correlation_result,
                rca=rca,
                recommendation=recommendation,
            ),
            prompt_summary=f"Question: '{user_question}'",
        )

    def _execute_with_fallback(
        self,
        operation_name: str,
        method_caller,
        fallback_caller,
        prompt_summary: str,
    ):
        """
        Helper enforcing structured logging, latency tracking, multi-provider execution, and deterministic fallback.
        """
        start_time = time.time()
        last_exception = None

        for provider in self._providers:
            prov_start = time.time()
            try:
                logger.info(f"Invoking LLM [{operation_name}] via provider: {provider.provider_name} ({provider.model_name})")
                result = method_caller(provider)
                duration = round(time.time() - prov_start, 3)

                # Check if provider returned internal fallback
                meta_provider = getattr(result, "metadata", None)
                used_fallback = False
                if meta_provider and hasattr(meta_provider, "provider_used"):
                    used_fallback = "Fallback" in str(meta_provider.provider_used)

                prompt_size = len(prompt_summary)
                completion_size = len(str(result))

                # MANDATORY INVOCATION LOG
                logger.info(
                    f"LLM Invocation Success | "
                    f"operation={operation_name} | "
                    f"provider={provider.provider_name} | "
                    f"model={provider.model_name} | "
                    f"latency={duration}s | "
                    f"prompt_size={prompt_size} | "
                    f"completion_size={completion_size} | "
                    f"fallback_used={used_fallback}"
                )
                return result

            except Exception as exc:
                duration = round(time.time() - prov_start, 3)
                last_exception = exc
                logger.warning(
                    f"LLM Invocation Failed | "
                    f"operation={operation_name} | "
                    f"provider={provider.provider_name} | "
                    f"model={provider.model_name} | "
                    f"latency={duration}s | "
                    f"exception={type(exc).__name__}: {exc}"
                )

        # Fallback to local rule engine if all registered providers fail
        fb_start = time.time()
        logger.info(f"Invoking Deterministic Fallback Engine for [{operation_name}] due to provider failures.")
        fb_result = fallback_caller()
        duration = round(time.time() - fb_start, 3)

        logger.info(
            f"LLM Invocation Fallback Completed | "
            f"operation={operation_name} | "
            f"provider={self._fallback_provider.provider_name} | "
            f"model={self._fallback_provider.model_name} | "
            f"latency={duration}s | "
            f"prompt_size={len(prompt_summary)} | "
            f"completion_size={len(str(fb_result))} | "
            f"fallback_used=True | "
            f"root_exception={last_exception}"
        )
        return fb_result
