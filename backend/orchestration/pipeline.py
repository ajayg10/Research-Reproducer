"""Pipeline orchestration - state machine for agent execution."""

import structlog
import uuid
from datetime import datetime
from typing import Optional

from backend.models.state import PipelineState, PipelineStatus
from backend.models.schemas import (
    PaperSpecification,
    ImplementationPlan,
    GeneratedImplementation,
    ExecutionResult,
    VerificationReport
)
from backend.agents import (
    parser_agent,
    planner_agent,
    codegen_agent,
    executor_agent,
    verifier_agent
)
from backend.services.storage import storage_service
from backend.orchestration.retry_logic import retry_manager


logger = structlog.get_logger()


class Pipeline:
    """Orchestrates the complete reproduction pipeline."""

    def __init__(self):
        """Initialize pipeline."""
        self.logger = logger

    async def start_reproduction(
        self,
        paper_source: str,
        paper_title: Optional[str] = None
    ) -> str:
        """
        Start a new reproduction pipeline.

        Args:
            paper_source: PDF path or arXiv URL
            paper_title: Optional paper title

        Returns:
            Pipeline ID
        """
        pipeline_id = str(uuid.uuid4())

        self.logger.info(
            "starting_pipeline",
            pipeline_id=pipeline_id,
            paper_source=paper_source
        )

        # Initialize pipeline state
        state = PipelineState(
            pipeline_id=pipeline_id,
            status=PipelineStatus.QUEUED,
            paper_source=paper_source
        )

        await storage_service.save_pipeline_state(state)

        # Start pipeline execution (don't await - run in background)
        import asyncio
        asyncio.create_task(self._execute_pipeline(pipeline_id))

        return pipeline_id

    async def _execute_pipeline(self, pipeline_id: str):
        """Execute the complete pipeline with retry logic."""
        try:
            state = await storage_service.load_pipeline_state(pipeline_id)
            if not state:
                self.logger.error("pipeline_state_not_found", pipeline_id=pipeline_id)
                return

            # STAGE 1: PARSING
            state.status = PipelineStatus.PARSING
            await storage_service.save_pipeline_state(state)

            parser_output = await parser_agent.run(
                input_data={"paper_source": state.paper_source},
                pipeline_id=pipeline_id
            )

            if not parser_output.success:
                await self._handle_failure(
                    state=state,
                    stage="parsing",
                    error=parser_output.error
                )
                return

            state.parser_output = parser_output.model_dump()
            await storage_service.save_pipeline_state(state)

            specification = parser_output.specification

            # STAGE 2: PLANNING
            state.status = PipelineStatus.PLANNING
            await storage_service.save_pipeline_state(state)

            planner_output = await planner_agent.run(
                input_data=specification,
                pipeline_id=pipeline_id
            )

            if not planner_output.success:
                await self._handle_failure(
                    state=state,
                    stage="planning",
                    error=planner_output.error
                )
                return

            state.planner_output = planner_output.model_dump()
            await storage_service.save_pipeline_state(state)

            plan = planner_output.plan

            # STAGE 3: CODE GENERATION
            state.status = PipelineStatus.GENERATING
            await storage_service.save_pipeline_state(state)

            codegen_output = await codegen_agent.run(
                input_data=plan,
                pipeline_id=pipeline_id
            )

            if not codegen_output.success:
                await self._handle_failure(
                    state=state,
                    stage="generating",
                    error=codegen_output.error
                )
                return

            state.codegen_output = codegen_output.model_dump()
            await storage_service.save_pipeline_state(state)

            # STAGE 4: EXECUTION (with retry support)
            execution_success = await self._execute_with_retry(
                state=state,
                codegen_output=codegen_output
            )

            if not execution_success:
                return

            # STAGE 5: VERIFICATION
            state.status = PipelineStatus.VERIFYING
            await storage_service.save_pipeline_state(state)

            verifier_output = await verifier_agent.run(
                input_data={
                    "specification": specification.model_dump(),
                    "execution_result": state.executor_output["result"]
                },
                pipeline_id=pipeline_id
            )

            if not verifier_output.success:
                await self._handle_failure(
                    state=state,
                    stage="verifying",
                    error=verifier_output.error
                )
                return

            state.verifier_output = verifier_output.model_dump()

            # Determine final status based on verification
            report = verifier_output.report
            if report.verdict.value == "successful":
                state.status = PipelineStatus.COMPLETED
            elif report.verdict.value in ["partial", "insufficient_info"]:
                state.status = PipelineStatus.PARTIAL
            else:
                state.status = PipelineStatus.FAILED

            await storage_service.save_pipeline_state(state)

            self.logger.info(
                "pipeline_completed",
                pipeline_id=pipeline_id,
                status=state.status.value,
                verdict=report.verdict.value
            )

        except Exception as e:
            self.logger.error(
                "pipeline_execution_error",
                pipeline_id=pipeline_id,
                error=str(e)
            )
            state.status = PipelineStatus.FAILED
            state.error = str(e)
            await storage_service.save_pipeline_state(state)

    async def _execute_with_retry(
        self,
        state: PipelineState,
        codegen_output
    ) -> bool:
        """Execute code with retry logic on failure."""
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            state.status = PipelineStatus.EXECUTING
            state.retry_count = attempt
            await storage_service.save_pipeline_state(state)

            self.logger.info(
                "execution_attempt",
                pipeline_id=state.pipeline_id,
                attempt=attempt + 1,
                max_retries=max_retries
            )

            executor_output = await executor_agent.run(
                input_data={
                    "workspace_path": codegen_output.workspace_path,
                    "entry_point": codegen_output.implementation.entry_point
                },
                pipeline_id=state.pipeline_id
            )

            state.executor_output = executor_output.model_dump()
            await storage_service.save_pipeline_state(state)

            if executor_output.success:
                self.logger.info(
                    "execution_successful",
                    pipeline_id=state.pipeline_id,
                    attempt=attempt + 1
                )
                return True

            # Execution failed - check if retry is appropriate
            self.logger.warning(
                "execution_failed",
                pipeline_id=state.pipeline_id,
                attempt=attempt + 1,
                error=executor_output.error
            )

            # Record retry history
            state.retry_history.append({
                "attempt": attempt + 1,
                "error": executor_output.error,
                "result": executor_output.model_dump()
            })

            # Check if should retry
            should_retry = await retry_manager.should_retry(
                error=executor_output.error,
                execution_result=executor_output.result,
                attempt=attempt
            )

            if not should_retry or attempt >= max_retries - 1:
                await self._handle_failure(
                    state=state,
                    stage="execution",
                    error=f"Execution failed after {attempt + 1} attempts"
                )
                return False

            # Retry with corrections
            state.status = PipelineStatus.RETRYING
            await storage_service.save_pipeline_state(state)

            # TODO: Implement correction logic (regenerate code with error feedback)
            # For MVP, just retry the same code
            attempt += 1

        return False

    async def _handle_failure(
        self,
        state: PipelineState,
        stage: str,
        error: Optional[str]
    ):
        """Handle pipeline failure."""
        self.logger.error(
            "pipeline_failed",
            pipeline_id=state.pipeline_id,
            stage=stage,
            error=error
        )

        state.status = PipelineStatus.FAILED
        state.error = error
        state.error_details = {"stage": stage}
        await storage_service.save_pipeline_state(state)

    async def get_status(self, pipeline_id: str) -> Optional[PipelineState]:
        """Get current pipeline status."""
        return await storage_service.load_pipeline_state(pipeline_id)


# Global pipeline instance
pipeline = Pipeline()
