# OldWorldColored 🎨

> Transform old black-and-white photos and videos into vibrant, full-color memories using AI — entirely in your browser.

[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%2018-61DAFB?logo=react)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ✨ Features

| Feature | Details |
|---|---|
| 🖼️ **Photo colorization** | Upload JPG, PNG, BMP, TIFF, or WEBP |
| 🎬 **Video colorization** | Upload MP4, AVI, MOV, or WEBM (up to 500 MB) |
| 🔄 **Interactive slider** | Drag to compare original vs. colorized side-by-side |
| 📈 **Real-time progress** | SSE-powered live progress bar during video processing |
| 📥 **One-click download** | Save your colorized result instantly |
| 🐳 **Docker-ready** | Single `docker compose up` spins up everything |

---

## 🖥️ Screenshots

```
┌──────────────────────────────────────────────────────────┐
│  ← Original B&W          Colorized ✨ →                  │
│  ┌────────────┬────────────────────────────────────────┐ │
│  │            │                                        │ │
│  │  grayscale │         full color                     │ │
│  │            │                                        │ │
│  └────────────┴────────────────────────────────────────┘ │
│              ◁◁ drag slider ▷▷                           │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/JAgbanwa/oldworldcolored.git
cd oldworldcolored
docker compose up --build
```

- Frontend: http://localhost:5173  
- Backend API: http://localhost:8000

The backend automatically downloads the ~130 MB model weights on first start.

---

### Option B — Manual (local dev)

#### Prerequisites
- Python 3.9+  
- Node.js 18+

#### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python download_models.py        # ~130 MB one-time download
uvicorn main:app --reload        # http://localhost:8000
```

#### 2. Frontend

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

The Vite dev server proxies `/api/*` → `http://localhost:8000` automatically.

---

## 🧠 How It Works

OldWorldColored uses the **"Colorful Image Colorization"** model by  
[Richard Zhang, Phillip Isola, Alexei A. Efros — ECCV 2016](https://richzhang.github.io/colorization/).

The model treats colorization as a **classification problem** in the CIE LAB color space:

1. The grayscale **L channel** is extracted from the input image.
2. A deep CNN predicts the **a and b color channels** using a distribution over 313 quantized color bins.
3. The predicted ab channels are combined with the original L channel and converted back to RGB.

This approach produces plausible, photorealistic colors without any manual hints.

**Video** processing runs the same model **frame-by-frame** with real-time SSE progress updates streamed to the browser.

---

## 📁 Project Structure

```
oldworldcolored/
├── backend/
│   ├── main.py              # FastAPI app — image, video, SSE, download endpoints
│   ├── colorizer.py         # Core colorization engine (OpenCV DNN)
│   ├── download_models.py   # One-time model weight downloader
│   ├── requirements.txt
│   ├── Dockerfile
│   └── models/              # Model weights (git-ignored, auto-downloaded)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main app — state machine & orchestration
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── UploadZone.jsx        # Drag-and-drop with preview
│   │   │   ├── ComparisonSlider.jsx  # Interactive before/after slider
│   │   │   ├── VideoResult.jsx       # Side-by-side video comparison
│   │   │   ├── ProcessingProgress.jsx
│   │   │   └── Footer.jsx
│   │   └── index.css         # Tailwind + custom slider/grain styles
│   ├── Dockerfile
│   ├── nginx.conf            # Reverse proxy for Docker prod
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

---

## 🔧 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Returns `{status, model_loaded}` |
| `POST` | `/api/colorize/image` | Upload image → returns `{download_url}` |
| `POST` | `/api/colorize/video` | Upload video → returns `{task_id}` |
| `GET` | `/api/progress/{task_id}` | SSE stream of `{status, progress, message}` |
| `GET` | `/api/download/{filename}` | Download colorized file |

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS 3, Framer Motion |
| Backend | FastAPI, Uvicorn, OpenCV DNN |
| Model | Zhang et al. (2016) Caffe model via OpenCV |
| Containers | Docker, Docker Compose, Nginx |

---

## 📄 License

MIT © [JAgbanwa](https://github.com/JAgbanwa)

---

## 🙏 Credits

- Colorization model: [Richard Zhang et al.](https://richzhang.github.io/colorization/) — ECCV 2016
- Icons: [Lucide](https://lucide.dev/)
- Animations: [Framer Motion](https://www.framer.com/motion/)
