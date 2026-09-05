"""
Inference Service.
Coordinates the end-to-end translation pipeline: upload storage,
preprocessing, ML forward pass, postprocessing, and database state recording.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.inference import InferenceJob, InferenceStatus
from app.services.storage_service import BaseStorageService, get_storage_service
from app.services.preprocessing_service import PreprocessingService
from app.services.postprocessing_service import PostprocessingService
from app.ml.predictor import Predictor
from app.core.config import settings
from app.core.logging import logger
from app.schemas.inference import InferenceJobResponseData


class InferenceService:
    """Orchestrates image translation lifecycle."""

    def __init__(
        self,
        db: AsyncSession,
        storage: Optional[BaseStorageService] = None,
    ):
        self.db = db
        self.storage = storage or get_storage_service()
        self.preprocessor = PreprocessingService(target_size=(settings.IMAGE_SIZE, settings.IMAGE_SIZE))
        self.postprocessor = PostprocessingService()

    async def execute_translation(
        self,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        model_version: Optional[str] = None,
    ) -> InferenceJobResponseData:
        """Executes full translation lifecycle."""
        ver = model_version or settings.ACTIVE_MODEL_VERSION
        ext = filename.split(".")[-1] if "." in filename else "png"

        # 1. Persist raw input in storage
        input_path = await self.storage.save_file(file_bytes, extension=ext, subfolder="uploads")

        # 2. Record initial job in database
        job = InferenceJob(
            user_id=user_id,
            input_image_path=input_path,
            original_filename=filename,
            model_version=ver,
            status=InferenceStatus.PROCESSING,
        )
        self.db.add(job)
        await self.db.flush()

        try:
            # 3. Preprocess
            input_tensor, detected_fmt, meta = self.preprocessor.process_upload(file_bytes, filename)
            job.image_format = detected_fmt

            # 4. ML Prediction
            predictor = Predictor(model_version=ver)
            pred_tensor, latency_ms = predictor.predict(input_tensor)

            # 5. Postprocess
            output_png_bytes, diff_png_bytes, _ = self.postprocessor.process_prediction(
                pred_tensor, input_tensor=input_tensor
            )

            # 6. Persist generated results
            output_path = await self.storage.save_file(output_png_bytes, extension="png", subfolder="results")
            diff_path = None
            if diff_png_bytes:
                diff_path = await self.storage.save_file(diff_png_bytes, extension="png", subfolder="results")

            # 7. Update Job Status
            job.output_image_path = output_path
            job.status = InferenceStatus.COMPLETED
            job.processing_time_ms = round(latency_ms, 2)
            job.completed_at = datetime.now(timezone.utc)
            job.metadata_json = {
                **meta,
                "difference_map_path": diff_path,
                "latency_ms": latency_ms,
                "device": str(predictor.registry.device),
            }

            await self.db.commit()
            await self.db.refresh(job)

            logger.info(
                f"Inference job {job.id} completed in {latency_ms:.1f}ms",
                extra={
                    "request_id": job.id,
                    "user_id": user_id,
                    "inference_duration_ms": latency_ms,
                    "model_version": ver,
                },
            )

            return self._build_response_data(job, diff_path)

        except Exception as e:
            job.status = InferenceStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            logger.error(f"Inference job {job.id} failed: {str(e)}", exc_info=True)
            raise

    def _build_response_data(self, job: InferenceJob, diff_path: Optional[str] = None) -> InferenceJobResponseData:
        diff = diff_path
        if not diff and job.metadata_json and "difference_map_path" in job.metadata_json:
            diff = job.metadata_json["difference_map_path"]

        return InferenceJobResponseData(
            id=job.id,
            user_id=job.user_id,
            status=job.status,
            model_version=job.model_version,
            original_filename=job.original_filename,
            image_format=job.image_format,
            input_image_url=self.storage.get_url(job.input_image_path),
            output_image_url=self.storage.get_url(job.output_image_path) if job.output_image_path else None,
            difference_map_url=self.storage.get_url(diff) if diff else None,
            processing_time_ms=job.processing_time_ms,
            created_at=job.created_at,
            completed_at=job.completed_at,
            metadata=job.metadata_json,
        )
