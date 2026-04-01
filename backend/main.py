"""
OldWorldColored – FastAPI backend
Endpoints:
  GET  /api/health
  POST /api/colorize/image
  POST /api/colorize/video   → returns task_id
  GET  /api/progress/{task_id}  → SSE stream
  GET  /api/download/{filename}
"""
import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from colorizer import Colorizer
from upscaler import Upscaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="OldWorldColored API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Directories ───────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Globals ───────────────────────────────────────────────────────────────────
colorizer: Optional[Colorizer] = None
upscaler: Optional[Upscaler] = None
task_store: dict = {}  # task_id → {"status", "progress", "message", "download_url"}

SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+\.(jpg|jpeg|png|bmp|mp4)$")

MAX_IMAGE_BYTES = 50 * 1024 * 1024   # 50 MB
MAX_VIDEO_BYTES = 500 * 1024 * 1024  # 500 MB

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/bmp", "image/tiff", "image/webp",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/webm",
}


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    global colorizer
    try:
        colorizer = Colorizer()
    except Exception as exc:
        logger.warning("Colorizer not ready – %s", exc)
        logger.warning("The model will be downloaded on the first request.")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "model_loaded": colorizer is not None}


# ── Image colorization ────────────────────────────────────────────────────────
@app.post("/api/colorize/image")
async def colorize_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enhance: bool = Form(False),
):
    _require_model()

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported image type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image exceeds 50 MB limit")

    task_id = str(uuid.uuid4())
    suffix = Path(file.filename or "upload.jpg").suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".bmp"}:
        suffix = ".jpg"

    # Store initial state BEFORE returning so SSE poll never hits 404
    task_store[task_id] = {"status": "queued", "progress": 0, "message": "Queued…"}

    background_tasks.add_task(_process_image_task, task_id, content, suffix, enhance)
    return {"task_id": task_id}


# ── Video colorization ────────────────────────────────────────────────────────
@app.post("/api/colorize/video")
async def colorize_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enhance: bool = Form(False),
):
    _require_model()

    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(400, f"Unsupported video type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_VIDEO_BYTES:
        raise HTTPException(413, "Video exceeds 500 MB limit")

    task_id = str(uuid.uuid4())
    suffix = Path(file.filename or "upload.mp4").suffix.lower()
    if suffix not in {".mp4", ".avi", ".mov", ".webm"}:
        suffix = ".mp4"

    input_path = UPLOAD_DIR / f"{task_id}_input{suffix}"
    output_path = OUTPUT_DIR / f"{task_id}_colorized.mp4"

    input_path.write_bytes(content)
    task_store[task_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Queued…",
    }

    background_tasks.add_task(
        _process_video_task, task_id, str(input_path), str(output_path), enhance
    )
    return {"task_id": task_id}


# ── SSE progress stream ───────────────────────────────────────────────────────
@app.get("/api/progress/{task_id}")
async def stream_progress(task_id: str):
    if task_id not in task_store:
        raise HTTPException(404, "Unknown task")

    async def event_gen():
        last_sent = None
        while True:
            data = task_store.get(task_id, {})
            payload = json.dumps(data)
            if payload != last_sent:
                yield f"data: {payload}\n\n"
                last_sent = payload
            if data.get("status") in ("completed", "failed"):
                break
            await asyncio.sleep(0.4)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ── Download ──────────────────────────────────────────────────────────────────
@app.get("/api/download/{filename}")
async def download_file(filename: str):
    if not SAFE_FILENAME_RE.match(filename):
        raise HTTPException(400, "Invalid filename")
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(path), filename=filename)


# ── Background image processor ────────────────────────────────────────────────
async def _process_image_task(task_id: str, content: bytes, suffix: str, enhance: bool):
    output_path = OUTPUT_DIR / f"{task_id}_colorized{suffix}"
    loop = asyncio.get_running_loop()
    try:
        task_store[task_id] = {"status": "processing", "progress": 5, "message": "Decoding image…"}

        img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Cannot decode image")

        task_store[task_id] = {"status": "processing", "progress": 10, "message": "Colorizing…"}
        # Run blocking colorization in thread so the event loop stays free
        colorized = await loop.run_in_executor(None, colorizer.colorize_frame, img)

        if enhance:
            _ensure_upscaler()

            def _upscale_with_progress() -> np.ndarray:
                def _cb(tile_pct: int) -> None:
                    overall = 40 + int(tile_pct * 0.55)  # maps 0→100 to 40→95
                    task_store[task_id] = {
                        "status": "processing",
                        "progress": overall,
                        "message": f"Enhancing resolution… {tile_pct}%",
                    }
                return upscaler.upscale(colorized, progress_cb=_cb)

            # Cap image size before ESRGAN — prevents OOM on large photos.
            # A 1024 px input → sharp 4096 px output (~16 MP). Larger wastes RAM.
            h_c, w_c = colorized.shape[:2]
            if max(h_c, w_c) > 1024:
                scale_f = 1024 / max(h_c, w_c)
                colorized = cv2.resize(
                    colorized,
                    (int(w_c * scale_f), int(h_c * scale_f)),
                    interpolation=cv2.INTER_LANCZOS4,
                )

            task_store[task_id] = {
                "status": "processing",
                "progress": 40,
                "message": "Starting super-resolution…",
            }
            colorized = await loop.run_in_executor(None, _upscale_with_progress)
        else:
            task_store[task_id] = {"status": "processing", "progress": 80, "message": "Saving…"}

        task_store[task_id] = {"status": "processing", "progress": 96, "message": "Encoding output…"}
        ok, buf = cv2.imencode(suffix, colorized)
        if not ok:
            raise ValueError("Failed to encode image")
        output_path.write_bytes(buf.tobytes())

        task_store[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Done!",
            "download_url": f"/api/download/{output_path.name}",
        }
    except Exception as exc:
        logger.exception("Image processing failed: %s", exc)
        task_store[task_id] = {"status": "failed", "progress": 0, "message": str(exc)}


# ── Background video processor ────────────────────────────────────────────────
async def _process_video_task(task_id: str, input_path: str, output_path: str, enhance: bool = False):
    try:
        task_store[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Opening video…",
        }

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError("Cannot open video file")

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if enhance:
            _ensure_upscaler()

        scale = upscaler.SCALE if enhance else 1
        out_w, out_h = w * scale, h * scale

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (out_w, out_h))

        processed = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            colorized = colorizer.colorize_frame(frame)
            if enhance:
                colorized = upscaler.upscale(colorized)
            out.write(colorized)
            processed += 1
            pct = min(99, int(processed / total * 100))
            task_store[task_id] = {
                "status": "processing",
                "progress": pct,
                "message": f"Colorizing frame {processed}/{total}…",
            }
            # Yield to the event loop periodically
            if processed % 5 == 0:
                await asyncio.sleep(0)

        cap.release()
        out.release()

        task_store[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Done!",
            "download_url": f"/api/download/{Path(output_path).name}",
        }
    except Exception as exc:
        logger.exception("Video processing failed: %s", exc)
        task_store[task_id] = {
            "status": "failed",
            "progress": 0,
            "message": str(exc),
        }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _require_model():
    if colorizer is None:
        raise HTTPException(
            503,
            detail=(
                "Model weights are still loading. Please wait a moment and retry."
            ),
        )


def _ensure_upscaler():
    global upscaler
    if upscaler is None:
        upscaler = Upscaler()
