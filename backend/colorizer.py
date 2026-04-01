"""
Core colorization engine — self-contained PyTorch implementation.

Reference: "Colorful Image Colorization" Zhang et al., ECCV 2016.
Model weights are downloaded from AWS S3 (~56 MB) and cached locally.
No external 'colorizers' package needed.
"""
import logging
import os
import urllib.request

import cv2
import numpy as np
import skimage.color as color
import torch
import torch.nn as nn
import torch.nn.functional as F
from skimage.transform import resize as sk_resize

logger = logging.getLogger(__name__)

# AWS S3 source — same URL used by the original authors
_MODEL_URL = (
    "https://colorizers.s3.us-east-2.amazonaws.com/"
    "colorization_release_v2-9b330a0b.pth"
)
_CACHE_DIR = os.path.expanduser("~/.cache/oldworldcolored")
_MODEL_FILENAME = "colorization_release_v2.pth"


# ── ECCV16 network ─────────────────────────────────────────────────────────────
class _ECCVGenerator(nn.Module):
    """
    Verbatim PyTorch port of the Zhang et al. (2016) ECCV colorization network.
    Input:  1×H×W  (L channel, normalised internally)
    Output: 2×H×W  (predicted a, b channels, unnormalised)
    """

    def __init__(self, norm_layer=nn.BatchNorm2d):
        super().__init__()
        self.model1 = nn.Sequential(
            nn.Conv2d(1, 64, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(64, 64, 3, 2, 1), nn.ReLU(True),
            norm_layer(64),
        )
        self.model2 = nn.Sequential(
            nn.Conv2d(64, 128, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(128, 128, 3, 2, 1), nn.ReLU(True),
            norm_layer(128),
        )
        self.model3 = nn.Sequential(
            nn.Conv2d(128, 256, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(256, 256, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(256, 256, 3, 2, 1), nn.ReLU(True),
            norm_layer(256),
        )
        self.model4 = nn.Sequential(
            nn.Conv2d(256, 512, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 1), nn.ReLU(True),
            norm_layer(512),
        )
        self.model5 = nn.Sequential(
            nn.Conv2d(512, 512, 3, 1, 2, dilation=2), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 2, dilation=2), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 2, dilation=2), nn.ReLU(True),
            norm_layer(512),
        )
        self.model6 = nn.Sequential(
            nn.Conv2d(512, 512, 3, 1, 2, dilation=2), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 2, dilation=2), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 2, dilation=2), nn.ReLU(True),
            norm_layer(512),
        )
        self.model7 = nn.Sequential(
            nn.Conv2d(512, 512, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(512, 512, 3, 1, 1), nn.ReLU(True),
            norm_layer(512),
        )
        self.model8 = nn.Sequential(
            nn.ConvTranspose2d(512, 256, 4, 2, 1), nn.ReLU(True),
            nn.Conv2d(256, 256, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(256, 256, 3, 1, 1), nn.ReLU(True),
            nn.Conv2d(256, 313, 1, 1, 0),
        )
        self.softmax = nn.Softmax(dim=1)
        self.model_out = nn.Conv2d(313, 2, 1, 1, 0, bias=False)
        self.upsample4 = nn.Upsample(scale_factor=4, mode="bilinear", align_corners=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = (x - 50.0) / 100.0          # normalise L
        x = self.model8(self.model7(self.model6(
            self.model5(self.model4(self.model3(self.model2(self.model1(x)))))
        )))
        return self.upsample4(self.model_out(self.softmax(x))) * 110.0


# ── Weight download ─────────────────────────────────────────────────────────────
def _ensure_weights() -> str:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    dest = os.path.join(_CACHE_DIR, _MODEL_FILENAME)
    if os.path.exists(dest):
        return dest

    logger.info("Downloading colorization weights from AWS S3 (~56 MB)…")

    def _hook(count, block, total):
        if total > 0:
            print(f"\r  {min(100, int(count * block * 100 / total))}%",
                  end="", flush=True)

    urllib.request.urlretrieve(_MODEL_URL, dest, _hook)
    print("\r  Download complete.                ")
    return dest


# ── Public API ──────────────────────────────────────────────────────────────────
class Colorizer:
    """Load the ECCV16 model and colorize individual BGR frames."""

    def __init__(self):
        logger.info("Initialising Colorizer (downloading weights if needed)…")
        weights_path = _ensure_weights()
        self._net = _ECCVGenerator()
        state = torch.load(weights_path, map_location="cpu")
        self._net.load_state_dict(state)
        self._net.eval()
        logger.info("Colorizer ready.")

    def colorize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Colorize a single BGR uint8 frame; returns a BGR uint8 frame."""
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype("float32") / 255.0

        lab_orig = color.rgb2lab(rgb)
        lab_rs = color.rgb2lab(
            sk_resize(rgb, (256, 256), anti_aliasing=True).astype("float32")
        )

        l_orig = torch.from_numpy(lab_orig[:, :, 0]).float()[None, None]
        l_rs = torch.from_numpy(lab_rs[:, :, 0]).float()[None, None]

        with torch.no_grad():
            ab_pred = self._net(l_rs).cpu()           # 1×2×256×256

        H, W = l_orig.shape[2], l_orig.shape[3]
        ab_full = F.interpolate(
            ab_pred, size=(H, W), mode="bilinear", align_corners=False
        )

        lab_out = (
            torch.cat([l_orig, ab_full], dim=1)
            .squeeze(0).permute(1, 2, 0).numpy()
        )
        rgb_out = (color.lab2rgb(lab_out) * 255).clip(0, 255).astype("uint8")
        return cv2.cvtColor(rgb_out, cv2.COLOR_RGB2BGR)
