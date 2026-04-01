# OldWorldColored 🎨

> Transform old black-and-white photos and videos into vibrant, full-color memories using AI — entirely in your browser.

[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%2018-61DAFB?logo=react)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/AI-PyTorch-EE4C2C?logo=pytorch)](https://pytorch.org/)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ✨ Features

| Feature | Details |
|---|---|
| 🖼️ **Photo colorization** | Upload JPG, PNG, BMP, TIFF, or WEBP (up to 50 MB) |
| 🎬 **Video colorization** | Upload MP4, AVI, MOV, or WEBM (up to 500 MB) |
| ✨ **Super Resolution (4×)** | One-click upscaling via Real-ESRGAN — output is 4× larger in each dimension |
| 🔄 **Interactive comparison slider** | Drag to compare original vs. colorized side-by-side |
| 📈 **Real-time progress bar** | SSE-powered live progress for both images and video (including per-tile SR progress) |
| 🌗 **Light / Dark mode** | Full theme toggle with system preference detection and localStorage persistence |
| 📥 **One-click download** | Save your colorized (and optionally upscaled) result instantly |
| 🐳 **Docker-ready** | Single `docker compose up --build` spins up everything |

---

## 🖥️ Preview

```
┌──────────────────────────────────────────────────────────┐
│  ← Original B&W          Colorized ✨ →                  │
│  ┌────────────┬────────────────────────────────────────┐ │
│  │            │                                        │ │
│  │  grayscale │         full color (4× upscaled)       │ │
│  │            │                                        │ │
│  └────────────┴────────────────────────────────────────┘ │
│              ◁◁ drag slider ▷▷                           │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Local)

### Docker Compose (recommended)

```bash
git clone https://github.com/JAgbanwa/oldworldcolored.git
cd oldworldcolored
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |

The backend automatically downloads both model weight files (~73 MB total) at build time.

---

### Manual (local dev)

#### Prerequisites
- Python 3.9+
- Node.js 18+

#### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
# Install PyTorch CPU-only first (much smaller than the CUDA build)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python download_models.py       # ~73 MB one-time download
uvicorn main:app --reload       # http://localhost:8000
```

#### 2. Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

---

## 🌐 Deploy to the Internet (Free — Render + Vercel)

### Step 1 — Deploy the backend to Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub account and select **JAgbanwa/oldworldcolored**
3. Render auto-detects `render.yaml` — confirm the service name is `oldworldcolored-api`
4. Click **Deploy** — model weights are baked in at build time
5. Copy your service URL → `https://oldworldcolored-api.onrender.com`

### Step 2 — Deploy the frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New → Project**
2. Import **JAgbanwa/oldworldcolored** from GitHub
3. Set **Root Directory** to `frontend`
4. Add environment variable:
   ```
   VITE_API_URL = https://oldworldcolored-api.onrender.com
   ```
5. Click **Deploy**

> **Note:** Render's free tier spins down after 15 min of inactivity. The first request after idle may take ~30 s to wake up.

---

## 🧠 How It Works

### Colorization — Zhang et al. (ECCV 2016)

OldWorldColored uses a **self-contained PyTorch port** of the  
[*Colorful Image Colorization*](https://richzhang.github.io/colorization/) network by Richard Zhang, Phillip Isola & Alexei A. Efros.

1. The grayscale **L channel** is extracted from the input image (CIE LAB color space).
2. A deep CNN predicts the **a and b color channels** as a distribution over 313 quantized color bins.
3. The predicted ab channels are recombined with the original L channel and converted back to RGB.

Weights (~56 MB) are downloaded from the author's own AWS S3 bucket and cached at `~/.cache/oldworldcolored/`.

### Super Resolution — Real-ESRGAN (6-block variant)

When **Super Resolution (4×)** is enabled, the colorized output is passed through a  
[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) **6-block RRDBNet** (the fast anime/photo variant).

- Model: `RealESRGAN_x4plus_anime_6B.pth` (~17 MB)
- Inference uses **512 px tiles** with 16 px overlap → bounded memory on any image size
- `torch.inference_mode()` + all CPU cores enabled for maximum throughput
- Per-tile progress is streamed live to the progress bar (40 % → 95 %)

### Progress Streaming

Both image and video jobs run as **background tasks** and report status through a **Server-Sent Events** (SSE) stream at `GET /api/progress/{task_id}`. The frontend subscribes immediately after upload so the bar moves in real time.

---

## 📁 Project Structure

```
oldworldcolored/
├── backend/
│   ├── main.py              # FastAPI app — image, video, SSE, download endpoints
│   ├── colorizer.py         # Zhang et al. ECCV 2016 colorization (PyTorch)
│   ├── upscaler.py          # Real-ESRGAN 6-block super-resolution (PyTorch)
│   ├── download_models.py   # Pre-downloads both model weight files
│   ├── start.sh             # Entrypoint (supports $PORT for Render)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # State machine & API orchestration
│   │   ├── ThemeContext.jsx           # Light / dark mode context + hook
│   │   ├── main.jsx
│   │   └── components/
│   │       ├── Header.jsx             # Nav + light/dark toggle
│   │       ├── UploadZone.jsx         # Drag-and-drop with file preview
│   │       ├── ComparisonSlider.jsx   # Interactive before/after slider
│   │       ├── VideoResult.jsx        # Side-by-side video comparison
│   │       ├── ProcessingProgress.jsx # Animated SSE progress bar
│   │       └── Footer.jsx
│   ├── Dockerfile
│   ├── nginx.conf            # Reverse proxy + 600 MB upload limit
│   └── package.json
│
├── render.yaml               # Render backend deployment config
├── docker-compose.yml
└── README.md
```

---

## 🔧 API Reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | — | `{status, model_loaded}` |
| `POST` | `/api/colorize/image` | `file` (image), `enhance` (bool) | Returns `{task_id}` |
| `POST` | `/api/colorize/video` | `file` (video), `enhance` (bool) | Returns `{task_id}` |
| `GET` | `/api/progress/{task_id}` | — | SSE stream of `{status, progress, message, download_url?}` |
| `GET` | `/api/download/{filename}` | — | Download colorized file |

Both colorize endpoints accept `enhance=true` to enable 4× Real-ESRGAN super-resolution after colorization.

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, Tailwind CSS 3 (`darkMode: "class"`), Framer Motion, Lucide |
| Backend | FastAPI 0.111, Uvicorn, OpenCV (headless), NumPy, Pillow |
| Colorization AI | Zhang et al. ECCV 2016 — self-contained PyTorch port, weights from AWS S3 |
| Super Resolution | Real-ESRGAN 6-block RRDBNet — weights from GitHub Releases (~17 MB) |
| ML Runtime | PyTorch (CPU-only), scikit-image |
| Containers | Docker, Docker Compose, Nginx (600 MB upload limit) |
| Deployment | Render (backend), Vercel (frontend) |

---

## 📄 License

MIT © [JAgbanwa](https://github.com/JAgbanwa)

---

## 🙏 Credits

- Colorization model: [Richard Zhang et al., ECCV 2016](https://richzhang.github.io/colorization/)
- Super-resolution model: [Xintao Wang — Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- Icons: [Lucide](https://lucide.dev/)
- Animations: [Framer Motion](https://www.framer.com/motion/)
