"""Agent 5: Verifier - Compares reproduced results with paper claims."""

import structlog
from typing import Dict, Any, List, Optional

from backend.agents.base import BaseAgent
from backend.models.state import AgentType
from backend.models.schemas import (
    VerifierOutput,
    VerificationReport,
    MetricComparison,
    ReproducibilityVerdict,
    DiscrepancyCategory,
    PaperSpecification,
    ExecutionResult
)


logger = structlog.get_logger()


class VerifierAgent(BaseAgent[Dict[str, Any], VerifierOutput]):
    """Agent that verifies reproduced results against paper claims."""

    def __init__(self):
        """Initialize Verifier agent."""
        super().__init__(AgentType.VERIFIER)

    async def execute(
        self,
        input_data: Dict[str, Any],
        pipeline_id: str
    ) -> VerifierOutput:
        """
        Verify reproduction results against paper claims.

        Args:
            input_data: Dict with 'specification', 'execution_result'
            pipeline_id: Pipeline identifier

        Returns:
            VerifierOutput with verification report
        """
        try:
            spec_dict = input_data.get("specification")
            exec_result_dict = input_data.get("execution_result")

            if not spec_dict or not exec_result_dict:
                return VerifierOutput(
                    success=False,
                    error="Missing specification or execution result"
                )

            # Reconstruct objects
            specification = PaperSpecification(**spec_dict)
            execution_result = ExecutionResult(**exec_result_dict)

            self.logger.info("starting_verification", paper=specification.title)

            # Compare metrics
            metric_comparisons = self._compare_metrics(
                claimed=specification.claimed_results,
                reproduced=execution_result.metrics
            )

            # Identify discrepancies
            discrepancies = self._identify_discrepancies(
                specification=specification,
                execution_result=execution_result,
                metric_comparisons=metric_comparisons
            )

            # Determine overall verdict
            verdict = self._determine_verdict(
                execution_result=execution_result,
                metric_comparisons=metric_comparisons
            )

            # Calculate quality score
            quality_score = self._calculate_quality_score(metric_comparisons)

            # Generate summary
            summary = self._generate_summary(
                verdict=verdict,
                metric_comparisons=metric_comparisons,
                discrepancies=discrepancies
            )

            report = VerificationReport(
                verdict=verdict,
                metric_comparisons=metric_comparisons,
                discrepancies=discrepancies,
                summary=summary,
                reproduction_quality_score=quality_score
            )

            self.logger.info(
                "verification_complete",
                verdict=verdict.value,
                quality_score=quality_score
            )

            return VerifierOutput(
                success=True,
                report=report
            )

        except Exception as e:
            self.logger.error("verifier_execution_error", error=str(e))
            return VerifierOutput(
                success=False,
                error=f"Verification failed: {str(e)}"
            )

    def _compare_metrics(
        self,
        claimed: List[Dict[str, Any]],
        reproduced: Dict[str, Any]
    ) -> List[MetricComparison]:
        """Compare claimed vs reproduced metrics."""
        comparisons = []

        # Create a mapping of claimed metrics
        claimed_map = {}
        for claim in claimed:
            metric_name = claim.get("metric", "").lower()
            value = claim.get("value")
            if metric_name and value is not None:
                claimed_map[metric_name] = float(value)

        # Compare each reproduced metric
        for metric_name, reproduced_value in reproduced.items():
            metric_name_lower = metric_name.lower()

            # Try to find matching claimed metric
            claimed_value = None
            for claimed_key in claimed_map:
                if claimed_key in metric_name_lower or metric_name_lower in claimed_key:
                    claimed_value = claimed_map[claimed_key]
                    break

            if claimed_value is None:
                # No claimed value found
                comparisons.append(MetricComparison(
                    metric_name=metric_name,
                    claimed_value=None,
                    reproduced_value=float(reproduced_value) if reproduced_value is not None else None,
                    status="UNKNOWN",
                    notes="No corresponding claimed metric found in paper"
                ))
                continue

            # Calculate differences
            try:
                reproduced_float = float(reproduced_value)
                claimed_float = float(claimed_value)

                abs_diff = abs(reproduced_float - claimed_float)
                rel_diff = abs_diff / claimed_float if claimed_float != 0 else float('inf')

                # Determine tolerance (configurable by metric type)
                tolerance = self._get_tolerance(metric_name)

                # Determine status
                status = "PASS" if rel_diff <= tolerance else "FAIL"

                comparisons.append(MetricComparison(
                    metric_name=metric_name,
                    claimed_value=claimed_float,
                    reproduced_value=reproduced_float,
                    absolute_difference=abs_diff,
                    relative_difference=rel_diff,
                    tolerance=tolerance,
                    status=status,
                    notes=""
                ))

            except (ValueError, TypeError) as e:
                comparisons.append(MetricComparison(
                    metric_name=metric_name,
                    claimed_value=claimed_value,
                    reproduced_value=reproduced_value,
                    status="UNKNOWN",
                    notes=f"Could not compare: {str(e)}"
                ))

        return comparisons

    def _get_tolerance(self, metric_name: str) -> float:
        """Get tolerance threshold for a metric."""
        metric_lower = metric_name.lower()

        # Accuracy metrics: ±2%
        if any(x in metric_lower for x in ["accuracy", "acc", "precision", "recall", "f1"]):
            return 0.02

        # Loss metrics: ±5%
        if "loss" in metric_lower:
            return 0.05

        # Default: ±2%
        return 0.02

    def _identify_discrepancies(
        self,
        specification: PaperSpecification,
        execution_result: ExecutionResult,
        metric_comparisons: List[MetricComparison]
    ) -> List[Dict[str, Any]]:
        """Identify reasons for discrepancies."""
        discrepancies = []

        # Check for execution failures
        if execution_result.status != "success":
            discrepancies.append({
                "category": DiscrepancyCategory.CODE_EXECUTION_FAILURE.value,
                "description": "Code execution failed",
                "details": execution_result.error
            })

        # Check for missing implementation details
        if specification.ambiguities:
            discrepancies.append({
                "category": DiscrepancyCategory.PAPER_AMBIGUITY.value,
                "description": "Paper contains ambiguous specifications",
                "details": specification.ambiguities
            })

        # Check for failed metrics
        failed_metrics = [m for m in metric_comparisons if m.status == "FAIL"]
        if failed_metrics:
            for metric in failed_metrics:
                discrepancies.append({
                    "category": DiscrepancyCategory.MISSING_IMPLEMENTATION_DETAIL.value,
                    "description": f"Metric '{metric.metric_name}' outside tolerance",
                    "details": {
                        "claimed": metric.claimed_value,
                        "reproduced": metric.reproduced_value,
                        "difference": metric.relative_difference
                    }
                })

        return discrepancies

    def _determine_verdict(
        self,
        execution_result: ExecutionResult,
        metric_comparisons: List[MetricComparison]
    ) -> ReproducibilityVerdict:
        """Determine overall reproducibility verdict."""
        # Execution failed
        if execution_result.status != "success":
            return ReproducibilityVerdict.EXECUTION_FAILED

        # No metrics to compare
        if not metric_comparisons:
            return ReproducibilityVerdict.INSUFFICIENT_INFO

        # Check metric statuses
        passed = sum(1 for m in metric_comparisons if m.status == "PASS")
        failed = sum(1 for m in metric_comparisons if m.status == "FAIL")
        total = len(metric_comparisons)

        # All passed
        if passed == total:
            return ReproducibilityVerdict.SUCCESSFUL

        # Some passed
        if passed > 0:
            return ReproducibilityVerdict.PARTIAL

        # All failed
        return ReproducibilityVerdict.FAILED

    def _calculate_quality_score(
        self,
        metric_comparisons: List[MetricComparison]
    ) -> Optional[float]:
        """Calculate 0-1 quality score."""
        if not metric_comparisons:
            return None

        passed = sum(1 for m in metric_comparisons if m.status == "PASS")
        return passed / len(metric_comparisons)

    def _generate_summary(
        self,
        verdict: ReproducibilityVerdict,
        metric_comparisons: List[MetricComparison],
        discrepancies: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable summary."""
        summary_parts = [f"REPRODUCIBILITY STATUS: {verdict.value.upper()}"]

        if metric_comparisons:
            summary_parts.append("\nMETRICS:")
            for comp in metric_comparisons:
                if comp.claimed_value is not None and comp.reproduced_value is not None:
                    summary_parts.append(
                        f"- {comp.metric_name}: "
                        f"Paper={comp.claimed_value:.4f}, "
                        f"Reproduced={comp.reproduced_value:.4f}, "
                        f"Diff={comp.relative_difference*100:.1f}%, "
                        f"Status={comp.status}"
                    )

        if discrepancies:
            summary_parts.append("\nDISCREPANCIES:")
            for disc in discrepancies[:3]:  # Top 3
                summary_parts.append(f"- {disc['description']}")

        return "\n".join(summary_parts)


# Global verifier agent instance
verifier_agent = VerifierAgent()
