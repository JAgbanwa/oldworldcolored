"""
Real-ESRGAN 4× Super-Resolution (fast 6-block variant)
=======================================================
Uses the official RRDBNet architecture with only 6 RRDB blocks
(RealESRGAN_x4plus_anime_6B.pth, ~17 MB) instead of the heavy 23-block model.
This is ~4× faster on CPU while still producing high-quality results.

Weights are downloaded from the author's GitHub releases on first use and
cached at ~/.cache/oldworldcolored/.

Reference: https://github.com/xinntao/Real-ESRGAN
"""

import math
import os
import urllib.request
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# ---------------------------------------------------------------------------
# Model download
# ---------------------------------------------------------------------------
_MODEL_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/"
    "v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
)
_CACHE_DIR = Path.home() / ".cache" / "oldworldcolored"
_CACHE_PATH = _CACHE_DIR / "RealESRGAN_x4plus_anime_6B.pth"


def _ensure_weights() -> Path:
    if _CACHE_PATH.exists():
        return _CACHE_PATH
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _CACHE_PATH.with_suffix(".tmp")
    try:
        print(f"[upscaler] Downloading Real-ESRGAN weights → {_CACHE_PATH}")
        urllib.request.urlretrieve(_MODEL_URL, str(tmp))
        tmp.rename(_CACHE_PATH)
        print("[upscaler] Download complete ✓")
    except Exception:
        if tmp.exists():
            os.remove(str(tmp))
        raise
    return _CACHE_PATH


# ---------------------------------------------------------------------------
# RRDB architecture — mirrors the official implementation exactly so weight
# keys match the published checkpoint without any renaming.
# ---------------------------------------------------------------------------


class _ResidualDenseBlock(nn.Module):
    def __init__(self, num_feat: int = 64, num_grow_ch: int = 32):
        super().__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class _RRDB(nn.Module):
    def __init__(self, num_feat: int = 64, num_grow_ch: int = 32):
        super().__init__()
        self.rdb1 = _ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = _ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = _ResidualDenseBlock(num_feat, num_grow_ch)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class _RRDBNet(nn.Module):
    """6-block RRDBNet — architecture used by RealESRGAN_x4plus_anime_6B.pth.
    Same structure as the 23-block model, just fewer RRDB blocks → much faster."""

    def __init__(
        self,
        num_in_ch: int = 3,
        num_out_ch: int = 3,
        num_feat: int = 64,
        num_block: int = 6,
        num_grow_ch: int = 32,
    ):
        super().__init__()
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.body = nn.Sequential(*[_RRDB(num_feat, num_grow_ch) for _ in range(num_block)])
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        # Two 2× nearest-neighbour upsample stages → 4× total
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.conv_first(x)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class Upscaler:
    """
    4× super-resolution for BGR uint8 images / video frames.

    Uses 512 px tiles (larger than before → fewer passes) with 16 px overlap.
    An optional progress_cb(pct: int) is called after each tile so callers
    can stream per-tile progress to the user.
    """

    SCALE = 4
    _TILE = 256   # 256 px keeps per-tile peak RAM under ~200 MB on CPU
    _PAD = 16

    def __init__(self) -> None:
        weights_path = _ensure_weights()
        self._model = _RRDBNet(num_block=6).eval()
        state = torch.load(weights_path, map_location="cpu")
        if isinstance(state, dict):
            state = state.get("params_ema") or state.get("params") or state
        self._model.load_state_dict(state, strict=True)
        # Use all available CPU cores for BLAS / convolution ops
        torch.set_num_threads(os.cpu_count() or 4)
        print("[upscaler] RealESRGAN 6-block (fast) loaded ✓")

    def upscale(
        self,
        bgr: np.ndarray,
        progress_cb: Optional[Callable[[int], None]] = None,
    ) -> np.ndarray:
        """Upscale a BGR uint8 ndarray by 4×. Returns BGR uint8.
        progress_cb receives 0-100 as tiles complete."""
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img_t = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)  # 1,3,H,W
        _, _, h, w = img_t.shape
        out_t = self._tile_inference(img_t, h, w, progress_cb)
        out_np = out_t.squeeze(0).permute(1, 2, 0).clamp(0, 1).numpy()
        out_bgr = cv2.cvtColor((out_np * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)
        return out_bgr

    @torch.inference_mode()
    def _tile_inference(
        self,
        img: torch.Tensor,
        h: int,
        w: int,
        progress_cb: Optional[Callable[[int], None]] = None,
    ) -> torch.Tensor:
        tile = self._TILE
        pad = self._PAD
        scale = self.SCALE

        # Small image: single forward pass
        if h <= tile and w <= tile:
            if progress_cb:
                progress_cb(100)
            return self._model(img)

        out = torch.zeros(1, 3, h * scale, w * scale)
        rows = math.ceil(h / tile)
        cols = math.ceil(w / tile)
        total = rows * cols
        done = 0

        for row in range(rows):
            for col in range(cols):
                x1, y1 = col * tile, row * tile
                x2, y2 = min(x1 + tile, w), min(y1 + tile, h)

                x1p = max(0, x1 - pad)
                y1p = max(0, y1 - pad)
                x2p = min(w, x2 + pad)
                y2p = min(h, y2 + pad)

                patch = img[:, :, y1p:y2p, x1p:x2p]
                sr = self._model(patch)

                tx1 = (x1 - x1p) * scale
                ty1 = (y1 - y1p) * scale
                tx2 = tx1 + (x2 - x1) * scale
                ty2 = ty1 + (y2 - y1) * scale

                out[:, :, y1 * scale : y2 * scale, x1 * scale : x2 * scale] = (
                    sr[:, :, ty1:ty2, tx1:tx2]
                )
                del sr, patch  # free tile memory immediately

                done += 1
                if progress_cb:
                    progress_cb(int(done / total * 100))

        return out
