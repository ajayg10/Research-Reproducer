"""Base agent class for all autonomous agents."""

import structlog
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from datetime import datetime

from backend.models.state import AgentType, AgentExecution


logger = structlog.get_logger()

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Base class for all agents in the system."""

    def __init__(self, agent_type: AgentType):
        """
        Initialize base agent.

        Args:
            agent_type: Type of agent (parser, planner, etc.)
        """
        self.agent_type = agent_type
        self.logger = logger.bind(agent=agent_type.value)

    @abstractmethod
    async def execute(self, input_data: InputT, pipeline_id: str) -> OutputT:
        """
        Execute agent logic.

        Args:
            input_data: Input data for this agent
            pipeline_id: Pipeline identifier for tracking

        Returns:
            Agent output
        """
        pass

    async def run(self, input_data: InputT, pipeline_id: str) -> OutputT:
        """
        Run agent with logging and error handling.

        Args:
            input_data: Input data
            pipeline_id: Pipeline ID

        Returns:
            Agent output
        """
        execution_id = f"{pipeline_id}_{self.agent_type.value}_{datetime.utcnow().timestamp()}"

        self.logger.info(
            "agent_execution_start",
            pipeline_id=pipeline_id,
            execution_id=execution_id
        )

        start_time = datetime.utcnow()

        try:
            output = await self.execute(input_data, pipeline_id)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.logger.info(
                "agent_execution_success",
                pipeline_id=pipeline_id,
                execution_id=execution_id,
                duration_seconds=duration
            )

            return output

        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.logger.error(
                "agent_execution_error",
                pipeline_id=pipeline_id,
                execution_id=execution_id,
                duration_seconds=duration,
                error=str(e),
                error_type=type(e).__name__
            )

            raise
