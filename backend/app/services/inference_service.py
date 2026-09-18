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
from app.services.volumetric_synthesizer import VolumetricSynthesizer
from app.schemas.inference import (
    InferenceJobResponseData,
    CTSliceItem,
    CTSliceSeriesResponse,
)


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
        self.volumetric_synthesizer = VolumetricSynthesizer(target_size=(settings.IMAGE_SIZE, settings.IMAGE_SIZE))

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

            # 5. Postprocess primary representations
            output_png_bytes, diff_png_bytes, _ = self.postprocessor.process_prediction(
                pred_tensor, input_tensor=input_tensor
            )

            # 6. Persist generated base results
            output_path = await self.storage.save_file(output_png_bytes, extension="png", subfolder="results")
            diff_path = None
            if diff_png_bytes:
                diff_path = await self.storage.save_file(diff_png_bytes, extension="png", subfolder="results")

            # 7. Synthesize Multi-Slice Volumetric CT Stack (16 Axial Slices)
            raw_slices = self.volumetric_synthesizer.synthesize_slice_series(
                base_ct_tensor=pred_tensor,
                input_xray_tensor=input_tensor,
            )
            saved_slices = []
            for sl in raw_slices:
                s_path = await self.storage.save_file(
                    sl["png_bytes"], extension="png", subfolder=f"slices/{job.id}"
                )
                saved_slices.append({
                    "slice_index": sl["slice_index"],
                    "total_slices": sl["total_slices"],
                    "z_position_mm": sl["z_position_mm"],
                    "relative_position": sl["relative_position"],
                    "anatomical_level": sl["anatomical_level"],
                    "description": sl["description"],
                    "suggested_window": sl["suggested_window"],
                    "mean_hu": sl["mean_hu"],
                    "tissue_predominance": sl["tissue_predominance"],
                    "storage_path": s_path,
                })

            # 8. Update Job Status & Metadata
            job.output_image_path = output_path
            job.status = InferenceStatus.COMPLETED
            job.processing_time_ms = round(latency_ms, 2)
            job.completed_at = datetime.now(timezone.utc)
            job.metadata_json = {
                **meta,
                "difference_map_path": diff_path,
                "latency_ms": latency_ms,
                "device": str(predictor.registry.device),
                "slices": saved_slices,
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

    async def get_or_generate_slices(self, job: InferenceJob) -> CTSliceSeriesResponse:
        """Retrieves or on-demand synthesizes the 16-slice volumetric CT stack for a job."""
        slices_meta = job.metadata_json.get("slices") if (job.metadata_json and isinstance(job.metadata_json, dict)) else None

        if not slices_meta:
            # Dynamically synthesize if not present from prior run
            input_bytes = await self.storage.get_file(job.input_image_path)
            input_tensor, _, _ = self.preprocessor.process_upload(input_bytes, job.original_filename or "input.png")
            predictor = Predictor(model_version=job.model_version or settings.ACTIVE_MODEL_VERSION)
            pred_tensor, _ = predictor.predict(input_tensor)

            raw_slices = self.volumetric_synthesizer.synthesize_slice_series(
                base_ct_tensor=pred_tensor,
                input_xray_tensor=input_tensor,
            )
            saved_slices = []
            for sl in raw_slices:
                s_path = await self.storage.save_file(
                    sl["png_bytes"], extension="png", subfolder=f"slices/{job.id}"
                )
                saved_slices.append({
                    "slice_index": sl["slice_index"],
                    "total_slices": sl["total_slices"],
                    "z_position_mm": sl["z_position_mm"],
                    "relative_position": sl["relative_position"],
                    "anatomical_level": sl["anatomical_level"],
                    "description": sl["description"],
                    "suggested_window": sl["suggested_window"],
                    "mean_hu": sl["mean_hu"],
                    "tissue_predominance": sl["tissue_predominance"],
                    "storage_path": s_path,
                })

            current_meta = dict(job.metadata_json or {})
            current_meta["slices"] = saved_slices
            job.metadata_json = current_meta
            await self.db.commit()
            await self.db.refresh(job)
            slices_meta = saved_slices

        items = [
            CTSliceItem(
                slice_index=s["slice_index"],
                total_slices=s["total_slices"],
                z_position_mm=s["z_position_mm"],
                relative_position=s["relative_position"],
                anatomical_level=s["anatomical_level"],
                description=s["description"],
                suggested_window=s["suggested_window"],
                mean_hu=s["mean_hu"],
                tissue_predominance=s["tissue_predominance"],
                image_url=self.storage.get_url(s["storage_path"]),
            )
            for s in slices_meta
        ]

        scout_url = self.storage.get_url(job.input_image_path)
        return CTSliceSeriesResponse(
            job_id=job.id,
            total_slices=len(items),
            scout_image_url=scout_url,
            slices=items,
        )

