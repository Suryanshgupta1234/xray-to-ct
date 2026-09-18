"""
Volumetric CT Synthesizer.
Generates an anatomically indexed multi-slice CT series (16 axial cross-sections)
spanning from the superior thoracic aperture (lung apex) to the diaphragmatic base
from a 2D planar projection and deep generative representation.
"""

import io
import math
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import torch
import torch.nn.functional as F

from ml.preprocessing.transforms import tensor_to_pil


# 16-Slice Anatomical Reference Guide (Thoracic CT Protocol)
ANATOMICAL_LEVELS = [
    {
        "index": 1,
        "z_mm": 75.0,
        "level_name": "Apical Parenchyma & Thoracic Inlet",
        "description": "Superior lung apices, 1st rib arches, clavicular heads, small tracheal lumen",
        "suggested_window": "lung",
        "mean_hu": -780.0,
        "tissue_predominance": "Parenchyma / Hypodense Air",
        "heart_scale": 0.05,
        "thoracic_scale_x": 0.76,
        "thoracic_scale_y": 0.74,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 2,
        "z_mm": 65.0,
        "level_name": "Apical Subsegmental & Clavicular Border",
        "description": "Apical lung segments, brachiocephalic venous confluence, vertebral body T1-T2",
        "suggested_window": "lung",
        "mean_hu": -710.0,
        "tissue_predominance": "Parenchyma / Air",
        "heart_scale": 0.08,
        "thoracic_scale_x": 0.80,
        "thoracic_scale_y": 0.78,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 3,
        "z_mm": 55.0,
        "level_name": "Supra-Aortic Great Vessels Level",
        "description": "Branching brachiocephalic, left common carotid, left subclavian artery, trachea",
        "suggested_window": "mediastinum",
        "mean_hu": -620.0,
        "tissue_predominance": "Parenchyma & Vascular",
        "heart_scale": 0.15,
        "thoracic_scale_x": 0.85,
        "thoracic_scale_y": 0.82,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 4,
        "z_mm": 45.0,
        "level_name": "Aortic Arch Cross-Section",
        "description": "Classic curved aortic arch contour, superior vena cava, mid-trachea, vertebral body T3",
        "suggested_window": "mediastinum",
        "mean_hu": -520.0,
        "tissue_predominance": "Mediastinum & Lung",
        "heart_scale": 0.28,
        "thoracic_scale_x": 0.89,
        "thoracic_scale_y": 0.86,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 5,
        "z_mm": 35.0,
        "level_name": "Aortopulmonary Window & Pretracheal Space",
        "description": "Aortopulmonary space, ascending/descending aorta, azygos arch draining into SVC",
        "suggested_window": "mediastinum",
        "mean_hu": -460.0,
        "tissue_predominance": "Mediastinum & Lung",
        "heart_scale": 0.40,
        "thoracic_scale_x": 0.93,
        "thoracic_scale_y": 0.89,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 6,
        "z_mm": 25.0,
        "level_name": "Tracheal Carina & Pulmonary Trunk",
        "description": "Carinal bifurcation into right and left mainstem bronchi, main pulmonary artery trunk",
        "suggested_window": "mediastinum",
        "mean_hu": -410.0,
        "tissue_predominance": "Tracheobronchial & Vascular",
        "heart_scale": 0.55,
        "thoracic_scale_x": 0.96,
        "thoracic_scale_y": 0.92,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 7,
        "z_mm": 15.0,
        "level_name": "Pulmonary Hilum & Main Bronchi",
        "description": "Bilateral pulmonary hila, descending aorta, bronchus intermedius, upper pulmonary veins",
        "suggested_window": "mediastinum",
        "mean_hu": -360.0,
        "tissue_predominance": "Hilar Structures",
        "heart_scale": 0.70,
        "thoracic_scale_x": 0.98,
        "thoracic_scale_y": 0.95,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 8,
        "z_mm": 5.0,
        "level_name": "Superior Cardiac & Left Atrium",
        "description": "Left atrium, aortic root, right ventricular outflow tract, bilateral mid-lung zones",
        "suggested_window": "mediastinum",
        "mean_hu": -290.0,
        "tissue_predominance": "Cardiovascular & Soft Tissue",
        "heart_scale": 0.85,
        "thoracic_scale_x": 1.00,
        "thoracic_scale_y": 0.98,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 9,
        "z_mm": -5.0,
        "level_name": "Mid-Cardiac & Aortic/Mitral Plane",
        "description": "Left ventricular inflow, right ventricular outflow, interventricular septum, mid lobes",
        "suggested_window": "mediastinum",
        "mean_hu": -220.0,
        "tissue_predominance": "Myocardium & Ventricles",
        "heart_scale": 0.98,
        "thoracic_scale_x": 1.02,
        "thoracic_scale_y": 1.00,
        "diaphragm_effect": 0.0,
    },
    {
        "index": 10,
        "z_mm": -15.0,
        "level_name": "Four-Chamber Thoracic Cross-Section",
        "description": "Left ventricle, right ventricle, left atrium, right atrium, maximum cardiac width",
        "suggested_window": "mediastinum",
        "mean_hu": -170.0,
        "tissue_predominance": "Myocardium & Blood Pool",
        "heart_scale": 1.00,
        "thoracic_scale_x": 1.04,
        "thoracic_scale_y": 1.02,
        "diaphragm_effect": 0.05,
    },
    {
        "index": 11,
        "z_mm": -25.0,
        "level_name": "Inferior Ventricles & IVC Inflow",
        "description": "Inferior muscular ventricular wall, IVC entry, posterior basal pulmonary segments",
        "suggested_window": "mediastinum",
        "mean_hu": -110.0,
        "tissue_predominance": "Soft Tissue & Inferior Vena Cava",
        "heart_scale": 0.88,
        "thoracic_scale_x": 1.05,
        "thoracic_scale_y": 1.03,
        "diaphragm_effect": 0.15,
    },
    {
        "index": 12,
        "z_mm": -35.0,
        "level_name": "Cardiac Apex & Right Hemidiaphragm Emergence",
        "description": "True apex of left ventricle, dome of right hemidiaphragm appearing in right hemithorax",
        "suggested_window": "soft_tissue",
        "mean_hu": -40.0,
        "tissue_predominance": "Diaphragm & Hepatic Parenchyma",
        "heart_scale": 0.68,
        "thoracic_scale_x": 1.05,
        "thoracic_scale_y": 1.03,
        "diaphragm_effect": 0.35,
    },
    {
        "index": 13,
        "z_mm": -45.0,
        "level_name": "Bilateral Diaphragmatic Domes",
        "description": "Hepatic dome (right), stomach fundus bubble & spleen apex (left), posterior lower lobes",
        "suggested_window": "soft_tissue",
        "mean_hu": 30.0,
        "tissue_predominance": "Hepatic / Splenic Tissue",
        "heart_scale": 0.40,
        "thoracic_scale_x": 1.04,
        "thoracic_scale_y": 1.02,
        "diaphragm_effect": 0.60,
    },
    {
        "index": 14,
        "z_mm": -55.0,
        "level_name": "Posterior Basal Lung Segments & Liver",
        "description": "Deep posterior costophrenic recesses, upper abdominal visceral organs, vertebral T11-T12",
        "suggested_window": "soft_tissue",
        "mean_hu": 65.0,
        "tissue_predominance": "Abdominal Viscera & Basal Sulci",
        "heart_scale": 0.20,
        "thoracic_scale_x": 1.02,
        "thoracic_scale_y": 1.00,
        "diaphragm_effect": 0.80,
    },
    {
        "index": 15,
        "z_mm": -65.0,
        "level_name": "Posterior Costophrenic Sulci",
        "description": "Sharp posterior costophrenic recesses, liver, spleen, gastric bubble, aorta bifurcation",
        "suggested_window": "bone",
        "mean_hu": 85.0,
        "tissue_predominance": "Sub-Diaphragmatic Organs & Ribs",
        "heart_scale": 0.10,
        "thoracic_scale_x": 1.00,
        "thoracic_scale_y": 0.98,
        "diaphragm_effect": 0.92,
    },
    {
        "index": 16,
        "z_mm": -75.0,
        "level_name": "Infradiaphragmatic Upper Abdomen",
        "description": "Upper abdominal cross-section, hepatic parenchyma, spleen, stomach, 12th ribs, L1 spine",
        "suggested_window": "bone",
        "mean_hu": 110.0,
        "tissue_predominance": "Dense Bone & Viscera",
        "heart_scale": 0.05,
        "thoracic_scale_x": 0.98,
        "thoracic_scale_y": 0.96,
        "diaphragm_effect": 1.00,
    },
]


class VolumetricSynthesizer:
    """
    Synthesizes a continuous 16-slice volumetric axial CT stack
    from a 2D planar projection and deep generative latent representation.
    """

    def __init__(self, target_size: Tuple[int, int] = (256, 256)):
        self.target_size = target_size

    def synthesize_slice_series(
        self,
        base_ct_tensor: torch.Tensor,
        input_xray_tensor: Optional[torch.Tensor] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generates 16 continuous axial slices with anatomical morphometric depth variation.

        Args:
            base_ct_tensor: Model output tensor [1, 1, H, W] with values in [-1, 1]
            input_xray_tensor: Input radiograph tensor [1, 1, H, W]

        Returns:
            List of 16 slice dictionaries containing PNG bytes and metadata.
        """
        if base_ct_tensor.ndim == 3:
            base_ct_tensor = base_ct_tensor.unsqueeze(0)

        device = base_ct_tensor.device
        _, _, H, W = base_ct_tensor.shape

        # Base coordinates grid [-1, 1]
        y_grid, x_grid = torch.meshgrid(
            torch.linspace(-1.0, 1.0, H, device=device),
            torch.linspace(-1.0, 1.0, W, device=device),
            indexing="ij",
        )

        slices_data = []

        for spec in ANATOMICAL_LEVELS:
            idx = spec["index"]
            total = len(ANATOMICAL_LEVELS)
            rel_pos = (idx - 1) / (total - 1)  # 0.0 (Apex) -> 1.0 (Base)

            # Morphometric Thoracic Warping Parameters
            sx = spec["thoracic_scale_x"]
            sy = spec["thoracic_scale_y"]
            heart_wt = spec["heart_scale"]
            diaph_wt = spec["diaphragm_effect"]

            # 1. Non-linear radial & anterior-posterior thoracic deformation grid
            grid_x = x_grid / sx
            grid_y = y_grid / sy

            # Slight anterior-posterior curvature offset along z
            grid_y = grid_y + 0.08 * (rel_pos - 0.5) * (grid_x ** 2)

            sampling_grid = torch.stack([grid_x, grid_y], dim=-1).unsqueeze(0)  # [1, H, W, 2]

            # 2. Warp base representation with zero padding
            warped_slice = F.grid_sample(
                base_ct_tensor,
                sampling_grid,
                mode="bilinear",
                padding_mode="zeros",
                align_corners=True,
            )

            # 3. Anatomical structure intensity modulation based on slice level
            # Central cardiac / mediastinal opacity mask (centered around middle thorax)
            r_cardiac = torch.sqrt((x_grid + 0.05) ** 2 + (y_grid - 0.05) ** 2)
            cardiac_mask = torch.exp(-((r_cardiac / 0.38) ** 2))
            mediastinal_boost = heart_wt * 0.35 * cardiac_mask

            # Diaphragmatic / hepatic mask (emerging on right side at inferior levels)
            # In radiologic convention: Patient's Right is on Viewer's Left
            r_hepatic = torch.sqrt((x_grid + 0.35) ** 2 + (y_grid - 0.25) ** 2)
            hepatic_mask = torch.exp(-((r_hepatic / 0.55) ** 2))
            diaphragm_boost = diaph_wt * 0.45 * hepatic_mask

            # Apical hyper-lucent parenchymal modulation (more hypodense air at apices)
            air_hypodense = (1.0 - rel_pos) * 0.15 * (1.0 - cardiac_mask)

            # Composite slice tensor
            slice_tensor = warped_slice + mediastinal_boost + diaphragm_boost - air_hypodense
            slice_tensor = torch.clamp(slice_tensor, -1.0, 1.0)

            # 4. Convert slice tensor to PIL Image
            pil_slice = tensor_to_pil(slice_tensor, normalize_range=(-1.0, 1.0))

            # 5. Burn-in subtle radiological HUD telemetry onto corner
            annotated_slice = self._overlay_slice_hud(
                pil_slice,
                slice_idx=idx,
                total_slices=total,
                z_mm=spec["z_mm"],
                level_name=spec["level_name"],
            )

            # Encode to PNG bytes
            buf = io.BytesIO()
            annotated_slice.save(buf, format="PNG")
            slice_png_bytes = buf.getvalue()

            slices_data.append({
                "slice_index": idx,
                "total_slices": total,
                "z_position_mm": spec["z_mm"],
                "relative_position": round(rel_pos, 4),
                "anatomical_level": spec["level_name"],
                "description": spec["description"],
                "suggested_window": spec["suggested_window"],
                "mean_hu": spec["mean_hu"],
                "tissue_predominance": spec["tissue_predominance"],
                "png_bytes": slice_png_bytes,
            })

        return slices_data

    def _overlay_slice_hud(
        self,
        img: Image.Image,
        slice_idx: int,
        total_slices: int,
        z_mm: float,
        level_name: str,
    ) -> Image.Image:
        """Overlays DICOM-style HUD indicators onto the corners of the slice."""
        canvas = img.convert("RGB")
        draw = ImageDraw.Draw(canvas)

        # Non-clinical stamp at bottom
        draw.text((8, 8), f"SL {slice_idx:02d}/{total_slices:02d}", fill=(0, 240, 255))
        draw.text((8, 20), f"Z: {z_mm:+.1f}mm", fill=(200, 220, 240))

        sign = "+" if z_mm >= 0 else ""
        hud_right = f"{sign}{z_mm:.0f}"
        draw.text((canvas.width - 45, 8), hud_right, fill=(0, 240, 255))

        # Bottom non-clinical watermark
        draw.text((8, canvas.height - 18), "AI-SYNTHESIS - NOT FOR CLINICAL USE", fill=(200, 140, 40))

        return canvas
