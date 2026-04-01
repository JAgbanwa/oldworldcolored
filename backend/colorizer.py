"""
Core colorization engine using Zhang et al. (2016) deep learning model.
Reference: "Colorful Image Colorization" - ECCV 2016
Model hosted on AWS S3 via the `colorizers` PyPI package.
"""
import logging

import cv2
import numpy as np
import torch
from colorizers import eccv16, postprocess_tens, preprocess_img

logger = logging.getLogger(__name__)


class Colorizer:
    """Wraps the Zhang et al. ECCV16 colorization model via the `colorizers` package."""

    def __init__(self):
        logger.info("Loading colorization model (ECCV16 – downloading if needed)…")
        self.model = eccv16(pretrained=True).eval()
        logger.info("Colorization model ready.")

    def colorize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Colorize a single BGR frame.
        Returns a colorized BGR uint8 frame.
        """
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # BGR → RGB uint8
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # preprocess_img expects HxWx3 (uint8 or float)
        tens_l_orig, tens_l_rs = preprocess_img(rgb, HW=(256, 256))

        with torch.no_grad():
            out_ab = self.model(tens_l_rs).cpu()

        # postprocess_tens returns HxWx3 float [0, 1] RGB
        out_rgb = postprocess_tens(tens_l_orig, out_ab)
        out_bgr = cv2.cvtColor((out_rgb * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
        return out_bgr
