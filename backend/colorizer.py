"""
Core colorization engine using Zhang et al. (2016) deep learning model.
Reference: "Colorful Image Colorization" - ECCV 2016
"""
import os
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
PROTOTXT_PATH = os.path.join(MODELS_DIR, "colorization_deploy_v2.prototxt")
CAFFEMODEL_PATH = os.path.join(MODELS_DIR, "colorization_release_v2.caffemodel")
PTS_PATH = os.path.join(MODELS_DIR, "pts_in_hull.npy")


class Colorizer:
    """Wraps the Zhang et al. colorization model via OpenCV DNN."""

    def __init__(self):
        self.net = None
        self._load_model()

    def _load_model(self):
        missing = [
            p for p in [PROTOTXT_PATH, CAFFEMODEL_PATH, PTS_PATH]
            if not os.path.exists(p)
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing model files: {missing}. Run `python download_models.py`."
            )

        self.net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, CAFFEMODEL_PATH)
        pts = np.load(PTS_PATH)

        class8 = self.net.getLayerId("class8_ab")
        conv8 = self.net.getLayerId("conv8_313_rh")
        pts = pts.transpose().reshape(2, 313, 1, 1)
        self.net.getLayer(class8).blobs = [pts.astype("float32")]
        self.net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]

        logger.info("Colorization model loaded.")

    def colorize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Colorize a single BGR frame.

        The model converts grayscale L channel to ab channels in
        CIE LAB color space, producing a full-color BGR image.
        """
        # Ensure the frame is treated as grayscale input (ignore existing color)
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        scaled = frame.astype("float32") / 255.0
        lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)

        # Resize to network's expected input size (224x224)
        resized = cv2.resize(lab, (224, 224))
        L = cv2.split(resized)[0]
        L -= 50  # Zero-center per model training

        self.net.setInput(cv2.dnn.blobFromImage(L))
        ab = self.net.forward()[0, :, :, :].transpose((1, 2, 0))

        # Upscale ab prediction back to original resolution
        ab = cv2.resize(ab, (frame.shape[1], frame.shape[0]))

        L_orig = cv2.split(lab)[0]
        colorized_lab = np.concatenate((L_orig[:, :, np.newaxis], ab), axis=2)
        colorized_bgr = cv2.cvtColor(colorized_lab, cv2.COLOR_LAB2BGR)
        colorized_bgr = np.clip(colorized_bgr, 0, 1)
        return (colorized_bgr * 255).astype("uint8")
