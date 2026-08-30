"""Agent 2: Planner - Creates implementation plans from paper specifications."""

import structlog
from typing import Dict, Any

from backend.agents.base import BaseAgent
from backend.models.state import AgentType
from backend.models.schemas import PlannerOutput, ImplementationPlan, PaperSpecification
from backend.services.gemini_client import gemini_client


logger = structlog.get_logger()


class PlannerAgent(BaseAgent[PaperSpecification, PlannerOutput]):
    """Agent that creates concrete implementation plans from paper specifications."""

    def __init__(self):
        """Initialize Planner agent."""
        super().__init__(AgentType.PLANNER)

    async def execute(
        self,
        input_data: PaperSpecification,
        pipeline_id: str
    ) -> PlannerOutput:
        """
        Create implementation plan from paper specification.

        Args:
            input_data: PaperSpecification from Parser
            pipeline_id: Pipeline identifier

        Returns:
            PlannerOutput with implementation plan or error
        """
        try:
            specification = input_data

            self.logger.info(
                "creating_implementation_plan",
                paper_title=specification.title
            )

            # Build planning prompt
            prompt = self._build_planning_prompt(specification)

            # Call Gemini for structured planning
            plan = await gemini_client.generate_structured(
                prompt=prompt,
                response_schema=ImplementationPlan,
                temperature=0.3  # Moderate creativity for planning
            )

            if not plan:
                return PlannerOutput(
                    success=False,
                    error="Gemini failed to generate implementation plan"
                )

            self.logger.info(
                "plan_created",
                dependencies_count=len(plan.dependencies),
                assumptions_count=len(plan.assumptions)
            )

            return PlannerOutput(
                success=True,
                plan=plan
            )

        except Exception as e:
            self.logger.error("planner_execution_error", error=str(e))
            return PlannerOutput(
                success=False,
                error=f"Planner execution failed: {str(e)}"
            )

    def _build_planning_prompt(self, spec: PaperSpecification) -> str:
        """Build planning prompt from specification."""
        return f"""You are an implementation planner for a research reproducibility engine.

Create a concrete, executable implementation plan for the following paper.

PAPER SPECIFICATION:
Title: {spec.title}
Problem: {spec.problem_definition}

Architecture: {spec.architecture}
Hyperparameters: {spec.hyperparameters}
Dataset: {spec.dataset}
Evaluation: {spec.evaluation}
Claimed Results: {spec.claimed_results}

Ambiguities: {spec.ambiguities}

YOUR TASK:
Create a detailed implementation plan that includes:

1. PROJECT STRUCTURE
   - Required directories and files
   - Entry points (train.py, eval.py, etc.)

2. DEPENDENCIES
   - Python packages needed (PyTorch/TensorFlow, numpy, etc.)
   - Specific versions if critical

3. MODEL IMPLEMENTATION
   - Architecture details
   - Layer specifications
   - Forward pass logic

4. DATASET PIPELINE
   - Data loading strategy
   - Preprocessing steps
   - Train/val/test splits

5. TRAINING LOOP
   - Optimizer setup
   - Loss function
   - Training procedure
   - Checkpointing

6. EVALUATION LOOP
   - Metrics to compute
   - Evaluation procedure

7. REPRODUCIBILITY REQUIREMENTS
   - Random seeds
   - Deterministic operations
   - Configuration management

8. COMPUTATIONAL REQUIREMENTS
   - Expected runtime
   - Memory requirements
   - CPU sufficient or GPU needed

9. CATEGORIZATION
   - What is DIRECTLY specified by the paper
   - What must be INFERRED from standard practices
   - What ASSUMPTIONS are being made

CONSTRAINTS:
- Target execution time: under 10 minutes (MVP scope)
- Assume CPU-only execution
- Use standard datasets that can be auto-downloaded
- Keep model size small
- If paper uses large models/datasets, create a simplified version

Be specific and concrete. This plan will be directly used for code generation.
"""


# Global planner agent instance
planner_agent = PlannerAgent()
