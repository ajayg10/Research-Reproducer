"""Storage service with local and cloud support."""

import json
import aiofiles
import structlog
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from backend.config import settings
from backend.models.state import PipelineState


logger = structlog.get_logger()


class StorageService:
    """Abstracted storage service supporting local and cloud storage."""

    def __init__(self):
        """Initialize storage service."""
        self.storage_type = settings.storage_type
        self.storage_path = Path(settings.storage_path)
        self.pipelines_dir = self.storage_path / "pipelines"
        self.artifacts_dir = self.storage_path / "artifacts"

    async def initialize(self):
        """Initialize storage (create directories, etc.)."""
        if self.storage_type == "local":
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.pipelines_dir.mkdir(parents=True, exist_ok=True)
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
            logger.info("local_storage_initialized", path=str(self.storage_path))
        else:
            # TODO: Initialize GCS client
            logger.info("cloud_storage_initialized", bucket=settings.gcs_bucket)

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("storage_cleanup_complete")

    # ============================================================
    # PIPELINE STATE OPERATIONS
    # ============================================================

    async def save_pipeline_state(self, state: PipelineState) -> bool:
        """Save pipeline state."""
        try:
            state.updated_at = datetime.utcnow()
            state_dict = state.model_dump(mode='json')

            if self.storage_type == "local":
                file_path = self.pipelines_dir / f"{state.pipeline_id}.json"
                async with aiofiles.open(file_path, 'w') as f:
                    await f.write(json.dumps(state_dict, indent=2))

                logger.info("pipeline_state_saved", pipeline_id=state.pipeline_id)
                return True
            else:
                # TODO: Save to Firestore
                pass

        except Exception as e:
            logger.error(
                "save_pipeline_state_error",
                pipeline_id=state.pipeline_id,
                error=str(e)
            )
            return False

    async def load_pipeline_state(self, pipeline_id: str) -> Optional[PipelineState]:
        """Load pipeline state."""
        try:
            if self.storage_type == "local":
                file_path = self.pipelines_dir / f"{pipeline_id}.json"

                if not file_path.exists():
                    logger.warning("pipeline_state_not_found", pipeline_id=pipeline_id)
                    return None

                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    return PipelineState(**data)
            else:
                # TODO: Load from Firestore
                pass

        except Exception as e:
            logger.error(
                "load_pipeline_state_error",
                pipeline_id=pipeline_id,
                error=str(e)
            )
            return None

    async def list_pipelines(self, limit: int = 100) -> List[PipelineState]:
        """List recent pipelines."""
        pipelines = []

        try:
            if self.storage_type == "local":
                for file_path in self.pipelines_dir.glob("*.json"):
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        pipelines.append(PipelineState(**data))

                # Sort by created_at descending
                pipelines.sort(key=lambda p: p.created_at, reverse=True)
                return pipelines[:limit]
            else:
                # TODO: Query Firestore
                pass

        except Exception as e:
            logger.error("list_pipelines_error", error=str(e))

        return pipelines

    # ============================================================
    # ARTIFACT OPERATIONS
    # ============================================================

    async def save_artifact(
        self,
        pipeline_id: str,
        artifact_name: str,
        content: bytes
    ) -> Optional[str]:
        """Save an artifact (logs, generated code, etc.)."""
        try:
            if self.storage_type == "local":
                pipeline_dir = self.artifacts_dir / pipeline_id
                pipeline_dir.mkdir(parents=True, exist_ok=True)

                artifact_path = pipeline_dir / artifact_name
                async with aiofiles.open(artifact_path, 'wb') as f:
                    await f.write(content)

                logger.info(
                    "artifact_saved",
                    pipeline_id=pipeline_id,
                    artifact=artifact_name
                )
                return str(artifact_path)
            else:
                # TODO: Upload to GCS
                pass

        except Exception as e:
            logger.error(
                "save_artifact_error",
                pipeline_id=pipeline_id,
                artifact=artifact_name,
                error=str(e)
            )
            return None

    async def load_artifact(
        self,
        pipeline_id: str,
        artifact_name: str
    ) -> Optional[bytes]:
        """Load an artifact."""
        try:
            if self.storage_type == "local":
                artifact_path = self.artifacts_dir / pipeline_id / artifact_name

                if not artifact_path.exists():
                    return None

                async with aiofiles.open(artifact_path, 'rb') as f:
                    return await f.read()
            else:
                # TODO: Download from GCS
                pass

        except Exception as e:
            logger.error(
                "load_artifact_error",
                pipeline_id=pipeline_id,
                artifact=artifact_name,
                error=str(e)
            )
            return None


# Global storage service instance
storage_service = StorageService()
