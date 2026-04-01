import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Download, ImageIcon, Film, Wand2, RotateCcw, AlertCircle, Sparkles } from "lucide-react";

import Header from "./components/Header";
import Footer from "./components/Footer";
import UploadZone from "./components/UploadZone";
import ComparisonSlider from "./components/ComparisonSlider";
import VideoResult from "./components/VideoResult";
import ProcessingProgress from "./components/ProcessingProgress";

const API = import.meta.env.VITE_API_URL ?? "";

// ── State machine ─────────────────────────────────────────────────────────────
// idle → uploading → processing (video only) → done | error
//                 ↘ done (image — no SSE needed)

export default function App() {
  const [mode, setMode] = useState("image"); // "image" | "video"
  const [file, setFile] = useState(null);
  const [superRes, setSuperRes] = useState(false);

  // Processing state
  const [phase, setPhase] = useState("idle"); // idle | uploading | processing | done | error
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState({ status: "idle", progress: 0, message: "" });
  const [errorMsg, setErrorMsg] = useState("");

  // Result
  const [originalObjectUrl, setOriginalObjectUrl] = useState(null);
  const [colorizedUrl, setColorizedUrl] = useState(null); // blob URL for comparison

  const eventSourceRef = useRef(null);

  // ── Cleanup on unmount ──────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
      if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
    };
  }, []);

  // ── Mode switch: reset everything ──────────────────────────────────────────
  const switchMode = (m) => {
    if (m === mode) return;
    reset();
    setMode(m);
  };

  const reset = () => {
    eventSourceRef.current?.close();
    if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
    setFile(null);
    setPhase("idle");
    setTaskId(null);
    setProgress({ status: "idle", progress: 0, message: "" });
    setErrorMsg("");
    setOriginalObjectUrl(null);
    setColorizedUrl(null);
  };

  // ── File selected ──────────────────────────────────────────────────────────
  const handleFile = useCallback(
    (f) => {
      setFile(f);
      if (!f) return;
      if (originalObjectUrl) URL.revokeObjectURL(originalObjectUrl);
      setOriginalObjectUrl(URL.createObjectURL(f));
    },
    [originalObjectUrl]
  );

  // ── Upload & colorize ──────────────────────────────────────────────────────
  const colorize = async () => {
    if (!file) return;
    setPhase("uploading");
    setErrorMsg("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("enhance", superRes ? "true" : "false");

    const endpoint = mode === "image" ? "/api/colorize/image" : "/api/colorize/video";

    try {
      setProgress({ status: "queued", progress: 0, message: "Uploading…" });
      const { data } = await axios.post(`${API}${endpoint}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          const pct = e.total ? Math.round((e.loaded / e.total) * 30) : 0;
          setProgress({ status: "queued", progress: pct, message: "Uploading…" });
        },
      });

      setTaskId(data.task_id);
      setPhase("processing");
      startSSE(data.task_id);
    } catch (err) {
      const msg =
        err.response?.data?.detail ??
        err.message ??
        "An unexpected error occurred.";
      setErrorMsg(msg);
      setPhase("error");
    }
  };

  // ── SSE progress for video ────────────────────────────────────────────────
  const startSSE = (id) => {
    eventSourceRef.current?.close();
    const es = new EventSource(`${API}/api/progress/${id}`);

    es.onmessage = async (e) => {
      const data = JSON.parse(e.data);
      setProgress(data);

      if (data.status === "completed") {
        es.close();
        // Fetch colorized video
        const resp = await axios.get(`${API}${data.download_url}`, {
          responseType: "blob",
        });
        setColorizedUrl(URL.createObjectURL(resp.data));
        setPhase("done");
      } else if (data.status === "failed") {
        es.close();
        setErrorMsg(data.message ?? "Processing failed.");
        setPhase("error");
      }
    };

    es.onerror = () => {
      es.close();
      setErrorMsg("Lost connection to server. Please retry.");
      setPhase("error");
    };

    eventSourceRef.current = es;
  };

  // ── Download helper ───────────────────────────────────────────────────────
  const downloadResult = () => {
    if (!colorizedUrl) return;
    const a = document.createElement("a");
    a.href = colorizedUrl;
    a.download = `colorized_${file?.name ?? "result"}`;
    a.click();
  };

  const isProcessing =
    phase === "uploading" || phase === "processing";

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 mx-auto w-full max-w-4xl px-4 py-12 sm:px-6">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10 text-center"
        >
          <h2 className="font-display text-4xl font-bold leading-tight dark:text-white text-zinc-900 sm:text-5xl">
            Bring history{" "}
            <span className="bg-gradient-to-r from-sepia-400 via-gold-400 to-amber-300 bg-clip-text text-transparent">
              to life
            </span>
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base dark:text-zinc-400 text-zinc-500">
            Upload a black-and-white photo or video and watch our AI breathe
            color into every pixel using{" "}
            <span className="dark:text-zinc-300 text-zinc-700">deep learning</span>.
          </p>
        </motion.div>

        {/* Mode tabs */}
        <div className="mb-6 flex justify-center">
          <div className="inline-flex rounded-xl border dark:border-zinc-800 border-zinc-300 dark:bg-zinc-900 bg-white p-1 shadow-sm">
            {[
              { id: "image", label: "Photo", Icon: ImageIcon },
              { id: "video", label: "Video", Icon: Film },
            ].map(({ id, label, Icon }) => (
              <button
                key={id}
                onClick={() => switchMode(id)}
                disabled={isProcessing}
                className={`
                  flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-medium transition-all duration-200
                  ${
                    mode === id
                      ? "bg-gradient-to-r from-sepia-600 to-gold-600 text-white shadow-md"
                      : "dark:text-zinc-400 text-zinc-500 dark:hover:text-zinc-200 hover:text-zinc-800"
                  }
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Upload card */}
        <AnimatePresence mode="wait">
          {phase === "idle" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              className="rounded-2xl border dark:border-zinc-800 border-zinc-200 dark:bg-zinc-900/60 bg-white/80 p-6 shadow-xl backdrop-blur-sm"
            >
              <UploadZone mode={mode} onFile={handleFile} disabled={isProcessing} />

              {/* Super-resolution toggle — always visible */}
              <div className="mt-5 flex flex-col items-center gap-2">
                <button
                  onClick={() => setSuperRes((v) => !v)}
                  disabled={isProcessing}
                  className={`
                    flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium
                    transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
                    ${
                      superRes
                        ? "border-amber-500/60 bg-amber-500/10 text-amber-400 shadow-sm shadow-amber-900/20"
                        : "dark:border-zinc-700 border-zinc-300 dark:text-zinc-400 text-zinc-500 dark:hover:border-zinc-500 hover:border-zinc-400 dark:hover:text-zinc-200 hover:text-zinc-800"
                    }
                  `}
                >
                  <Sparkles className="h-4 w-4" />
                  Super Resolution (4×)
                  {superRes ? (
                    <span className="ml-1 rounded-full bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-400">
                      ON
                    </span>
                  ) : (
                    <span className="ml-1 rounded-full dark:bg-zinc-800 bg-zinc-200 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider dark:text-zinc-500 text-zinc-400">
                      OFF
                    </span>
                  )}
                </button>

                {superRes && (
                  <p className="text-center text-xs dark:text-zinc-500 text-zinc-400">
                    Output will be 4× larger using Real-ESRGAN deep learning upscaling.
                  </p>
                )}
                {superRes && mode === "video" && (
                  <p className="text-center text-xs text-amber-600 dark:text-amber-500">
                    ⚠ Super Resolution on video is very slow — each frame is upscaled 4×. Best for short clips.
                  </p>
                )}
              </div>

              {file && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 flex justify-center"
                >
                  <button
                    onClick={colorize}
                    disabled={isProcessing}
                    className="
                      flex items-center gap-2 rounded-xl bg-gradient-to-r from-sepia-600 to-gold-600
                      px-8 py-3 font-semibold text-white shadow-lg shadow-amber-900/30
                      transition hover:from-sepia-500 hover:to-gold-500 hover:shadow-amber-900/50
                      active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed
                    "
                  >
                    <Wand2 className="h-5 w-5" />
                    {superRes ? "Colorize & Enhance" : `Colorize ${mode === "image" ? "Photo" : "Video"}`}
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}

          {/* Progress */}
          {(phase === "uploading" || phase === "processing") && (
            <motion.div
              key="progress"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <ProcessingProgress
                status={progress.status}
                progress={progress.progress}
                message={progress.message}
              />
              {mode === "video" && (
                <p className="mt-3 text-center text-xs dark:text-zinc-600 text-zinc-400">
                  Video colorization may take a few minutes depending on length.
                </p>
              )}
            </motion.div>
          )}

          {/* Error */}
          {phase === "error" && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-2xl border border-red-800/40 bg-red-950/30 p-6 text-center"
            >
              <AlertCircle className="mx-auto mb-3 h-10 w-10 text-red-400" />
              <p className="font-semibold text-red-400 dark:text-red-300">Something went wrong</p>
              <p className="mt-1 text-sm text-red-500">{errorMsg}</p>
              <button
                onClick={reset}
                className="mt-4 flex items-center gap-2 mx-auto rounded-lg border dark:border-zinc-700 border-zinc-300 px-4 py-2 text-sm dark:text-zinc-300 text-zinc-600 dark:hover:text-white hover:text-zinc-900 dark:hover:border-zinc-500 hover:border-zinc-500 transition"
              >
                <RotateCcw className="h-4 w-4" /> Try again
              </button>
            </motion.div>
          )}

          {/* Result */}
          {phase === "done" && colorizedUrl && (
            <motion.div
              key="result"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6"
            >
              {mode === "image" ? (
                <ComparisonSlider
                  before={originalObjectUrl}
                  after={colorizedUrl}
                />
              ) : (
                <VideoResult
                  originalUrl={originalObjectUrl}
                  colorizedUrl={colorizedUrl}
                />
              )}

              {/* Action row */}
              <div className="flex flex-wrap items-center justify-center gap-4">
                <button
                  onClick={downloadResult}
                  className="
                    flex items-center gap-2 rounded-xl bg-gradient-to-r from-sepia-600 to-gold-600
                    px-6 py-2.5 font-semibold text-white shadow-lg
                    transition hover:from-sepia-500 hover:to-gold-500 active:scale-95
                  "
                >
                  <Download className="h-4 w-4" />
                  Download colorized {mode === "image" ? "photo" : "video"}
                </button>
                <button
                  onClick={reset}
                  className="flex items-center gap-2 rounded-xl border dark:border-zinc-700 border-zinc-300 px-6 py-2.5 text-sm dark:text-zinc-300 text-zinc-600 transition dark:hover:border-zinc-500 hover:border-zinc-400 dark:hover:text-white hover:text-zinc-900"
                >
                  <RotateCcw className="h-4 w-4" /> Colorize another
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </div>
  );
}
