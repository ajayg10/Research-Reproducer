"""Agent 4: Executor - Runs generated code in isolated Docker sandbox."""

import structlog
import docker
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any

from backend.agents.base import BaseAgent
from backend.models.state import AgentType
from backend.models.schemas import ExecutorOutput, ExecutionResult, GeneratedImplementation
from backend.config import settings


logger = structlog.get_logger()


class ExecutorAgent(BaseAgent[Dict[str, Any], ExecutorOutput]):
    """Agent that executes generated code in an isolated Docker sandbox."""

    def __init__(self):
        """Initialize Executor agent."""
        super().__init__(AgentType.EXECUTOR)
        try:
            self.docker_client = docker.from_env()
            logger.info("docker_client_initialized")
        except Exception as e:
            logger.error("docker_client_initialization_failed", error=str(e))
            self.docker_client = None

    async def execute(
        self,
        input_data: Dict[str, Any],
        pipeline_id: str
    ) -> ExecutorOutput:
        """
        Execute generated code in Docker sandbox.

        Args:
            input_data: Dict with 'workspace_path' and 'entry_point'
            pipeline_id: Pipeline identifier

        Returns:
            ExecutorOutput with execution results or error
        """
        if not self.docker_client:
            return ExecutorOutput(
                success=False,
                error="Docker client not available. Is Docker running?"
            )

        workspace_path = input_data.get("workspace_path")
        entry_point = input_data.get("entry_point", "train.py")

        if not workspace_path:
            return ExecutorOutput(
                success=False,
                error="No workspace path provided"
            )

        try:
            workspace = Path(workspace_path)
            if not workspace.exists():
                return ExecutorOutput(
                    success=False,
                    error=f"Workspace not found: {workspace_path}"
                )

            self.logger.info(
                "starting_sandbox_execution",
                workspace=workspace_path,
                entry_point=entry_point
            )

            # Execute in sandbox
            result = await self._run_in_sandbox(
                workspace=workspace,
                entry_point=entry_point,
                pipeline_id=pipeline_id
            )

            return ExecutorOutput(
                success=result.status == "success",
                result=result,
                error=result.error if result.status != "success" else None
            )

        except Exception as e:
            self.logger.error("executor_execution_error", error=str(e))
            return ExecutorOutput(
                success=False,
                error=f"Executor failed: {str(e)}"
            )

    async def _run_in_sandbox(
        self,
        workspace: Path,
        entry_point: str,
        pipeline_id: str
    ) -> ExecutionResult:
        """Run code in Docker sandbox with resource limits."""
        start_time = time.time()

        try:
            # Build Docker command
            command = f"""
                set -e
                pip install -q -r requirements.txt 2>&1
                python {entry_point}
            """

            self.logger.info("creating_docker_container")

            # Create container with resource limits
            container = self.docker_client.containers.run(
                image="python:3.11-slim",
                command=["bash", "-c", command],
                volumes={
                    str(workspace.absolute()): {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },
                working_dir="/workspace",
                detach=True,
                network_mode="none" if not settings.sandbox_network_enabled else "bridge",
                mem_limit=settings.sandbox_memory_limit,
                cpu_quota=int(settings.sandbox_cpu_limit * 100000),
                cpu_period=100000,
                security_opt=["no-new-privileges"],
                user="nobody",  # Non-root execution
                remove=False  # Keep container for inspection
            )

            self.logger.info("container_started", container_id=container.id[:12])

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=settings.sandbox_timeout)
                exit_code = result['StatusCode']
            except Exception as timeout_err:
                self.logger.warning("execution_timeout", timeout=settings.sandbox_timeout)
                container.kill()
                exit_code = -1
                status = "timeout"

                runtime = time.time() - start_time

                return ExecutionResult(
                    status=status,
                    exit_code=exit_code,
                    runtime_seconds=runtime,
                    stdout="",
                    stderr=f"Execution timed out after {settings.sandbox_timeout}s",
                    error="Execution timeout"
                )

            # Capture logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')

            runtime = time.time() - start_time

            self.logger.info(
                "container_completed",
                exit_code=exit_code,
                runtime=runtime
            )

            # Try to extract metrics from generated files
            metrics = await self._extract_metrics(workspace)

            # Determine status
            if exit_code == 0:
                status = "success"
                error = None
            else:
                status = "failure"
                error = f"Process exited with code {exit_code}"

            # Clean up container
            container.remove()

            return ExecutionResult(
                status=status,
                exit_code=exit_code,
                runtime_seconds=runtime,
                stdout=stdout,
                stderr=stderr,
                metrics=metrics,
                artifacts=[],
                resource_usage={},
                error=error,
                error_traceback=stderr if exit_code != 0 else None
            )

        except docker.errors.ImageNotFound:
            return ExecutionResult(
                status="error",
                exit_code=-1,
                runtime_seconds=0,
                error="Docker image python:3.11-slim not found. Please pull it first."
            )

        except Exception as e:
            runtime = time.time() - start_time
            self.logger.error("sandbox_execution_error", error=str(e))

            return ExecutionResult(
                status="error",
                exit_code=-1,
                runtime_seconds=runtime,
                stderr=str(e),
                error=f"Sandbox execution error: {str(e)}"
            )

    async def _extract_metrics(self, workspace: Path) -> Dict[str, Any]:
        """Extract metrics from generated JSON files."""
        metrics = {}

        # Look for metrics.json (from training)
        metrics_file = workspace / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    train_metrics = json.load(f)
                    metrics.update(train_metrics)
            except Exception as e:
                self.logger.warning("failed_to_read_metrics", error=str(e))

        # Look for eval_metrics.json (from evaluation)
        eval_metrics_file = workspace / "eval_metrics.json"
        if eval_metrics_file.exists():
            try:
                with open(eval_metrics_file, 'r') as f:
                    eval_metrics = json.load(f)
                    metrics.update(eval_metrics)
            except Exception as e:
                self.logger.warning("failed_to_read_eval_metrics", error=str(e))

        return metrics


# Global executor agent instance
executor_agent = ExecutorAgent()
