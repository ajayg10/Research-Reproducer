"""Retry logic and self-correction for pipeline failures."""

import structlog
from typing import Optional

from backend.models.schemas import ExecutionResult


logger = structlog.get_logger()


class RetryManager:
    """Manages retry decisions and self-correction logic."""

    def __init__(self):
        """Initialize retry manager."""
        self.logger = logger

    async def should_retry(
        self,
        error: Optional[str],
        execution_result: Optional[ExecutionResult],
        attempt: int
    ) -> bool:
        """
        Determine if execution should be retried.

        Args:
            error: Error message from execution
            execution_result: Execution result object
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        if not error:
            return False

        # Don't retry after max attempts
        if attempt >= 2:  # 0, 1, 2 = 3 attempts total
            self.logger.info("max_retries_reached", attempt=attempt)
            return False

        # Analyze error to determine if retry is appropriate
        error_lower = error.lower()

        # Retry on transient errors
        if any(x in error_lower for x in [
            "timeout",
            "network",
            "connection",
            "temporarily unavailable"
        ]):
            self.logger.info("retrying_transient_error", error=error)
            return True

        # Retry on dependency installation failures
        if any(x in error_lower for x in [
            "package not found",
            "pip install",
            "requirement"
        ]):
            self.logger.info("retrying_dependency_error", error=error)
            return True

        # Don't retry on deterministic code errors
        if any(x in error_lower for x in [
            "syntax error",
            "import error",
            "name error",
            "type error",
            "value error"
        ]):
            self.logger.info("not_retrying_code_error", error=error)
            return False

        # Default: retry once
        if attempt == 0:
            self.logger.info("retrying_once", error=error)
            return True

        return False

    async def diagnose_failure(
        self,
        error: str,
        execution_result: ExecutionResult
    ) -> str:
        """
        Diagnose the root cause of a failure.

        Args:
            error: Error message
            execution_result: Execution result

        Returns:
            Diagnosis description
        """
        diagnoses = []

        # Check stderr for clues
        if execution_result.stderr:
            stderr_lower = execution_result.stderr.lower()

            if "modulenotfounderror" in stderr_lower:
                diagnoses.append("Missing Python module - dependency issue")

            if "cuda" in stderr_lower or "gpu" in stderr_lower:
                diagnoses.append("GPU-related error - code requires CUDA")

            if "filenotfounderror" in stderr_lower:
                diagnoses.append("Missing file - dataset or resource not found")

            if "out of memory" in stderr_lower:
                diagnoses.append("Out of memory - model or batch size too large")

        # Check exit code
        if execution_result.exit_code == 137:
            diagnoses.append("Process killed (OOM or timeout)")

        if execution_result.exit_code == 139:
            diagnoses.append("Segmentation fault")

        if not diagnoses:
            diagnoses.append("Unknown failure - manual investigation needed")

        return "; ".join(diagnoses)

    async def generate_correction_prompt(
        self,
        original_plan: dict,
        error: str,
        diagnosis: str
    ) -> str:
        """
        Generate a correction prompt for code regeneration.

        Args:
            original_plan: Original implementation plan
            error: Error message
            diagnosis: Failure diagnosis

        Returns:
            Correction prompt for LLM
        """
        prompt = f"""The previous implementation failed with the following error:

ERROR: {error}

DIAGNOSIS: {diagnosis}

ORIGINAL PLAN:
{original_plan}

Please generate a CORRECTED implementation that addresses this failure.

Specific corrections needed:
"""

        # Add specific correction instructions based on diagnosis
        if "dependency" in diagnosis.lower():
            prompt += "\n- Fix dependency specifications in requirements.txt"
            prompt += "\n- Ensure all imports are available"

        if "cuda" in diagnosis.lower() or "gpu" in diagnosis.lower():
            prompt += "\n- Make code CPU-compatible"
            prompt += "\n- Remove GPU-specific operations"

        if "memory" in diagnosis.lower():
            prompt += "\n- Reduce model size"
            prompt += "\n- Decrease batch size"
            prompt += "\n- Optimize memory usage"

        if "file" in diagnosis.lower() or "dataset" in diagnosis.lower():
            prompt += "\n- Fix dataset loading logic"
            prompt += "\n- Add dataset download logic"
            prompt += "\n- Handle missing files gracefully"

        prompt += "\n\nGenerate the complete corrected implementation."

        return prompt


# Global retry manager instance
retry_manager = RetryManager()
