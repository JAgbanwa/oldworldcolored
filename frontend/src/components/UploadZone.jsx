import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { ImageIcon, Film, Upload, X, AlertTriangle } from "lucide-react";

const ACCEPT_IMAGE = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/bmp": [".bmp"],
  "image/tiff": [".tiff", ".tif"],
  "image/webp": [".webp"],
};

const ACCEPT_VIDEO = {
  "video/mp4": [".mp4"],
  "video/avi": [".avi"],
  "video/quicktime": [".mov"],
  "video/webm": [".webm"],
  "video/x-msvideo": [".avi"],
};

export default function UploadZone({ mode, onFile, disabled }) {
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);

  const isImage = mode === "image";
  const accept = isImage ? ACCEPT_IMAGE : ACCEPT_VIDEO;
  const maxSize = isImage ? 20 * 1024 * 1024 : 500 * 1024 * 1024;

  const onDrop = useCallback(
    (accepted, rejected) => {
      setError(null);
      if (rejected.length > 0) {
        const err = rejected[0].errors[0];
        setError(
          err.code === "file-too-large"
            ? `File is too large. Max size is ${isImage ? "20 MB" : "500 MB"}.`
            : err.message
        );
        return;
      }
      if (accepted.length === 0) return;

      const file = accepted[0];
      if (isImage) {
        const url = URL.createObjectURL(file);
        setPreview({ type: "image", url });
      } else {
        const url = URL.createObjectURL(file);
        setPreview({ type: "video", url });
      }
      onFile(file);
    },
    [isImage, onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    multiple: false,
    disabled,
  });

  const clearPreview = (e) => {
    e.stopPropagation();
    if (preview) URL.revokeObjectURL(preview.url);
    setPreview(null);
    setError(null);
    onFile(null);
  };

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          relative flex min-h-[260px] cursor-pointer flex-col items-center justify-center
          rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300
          ${isDragActive ? "drop-active" : "border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/30"}
          ${disabled ? "pointer-events-none opacity-50" : ""}
        `}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {preview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              className="relative w-full"
            >
              {preview.type === "image" ? (
                <img
                  src={preview.url}
                  alt="Selected"
                  className="mx-auto max-h-48 rounded-xl object-contain shadow-lg"
                  style={{ filter: "grayscale(30%)" }}
                />
              ) : (
                <video
                  src={preview.url}
                  className="mx-auto max-h-48 w-full rounded-xl object-contain shadow-lg"
                  controls
                  muted
                />
              )}
              <button
                onClick={clearPreview}
                className="absolute -right-2 -top-2 rounded-full bg-zinc-700 p-1 text-zinc-300 shadow transition hover:bg-red-600 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
              <p className="mt-3 text-sm text-zinc-400">
                Click or drag to replace
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-4"
            >
              <div
                className={`rounded-2xl p-5 ${
                  isDragActive
                    ? "bg-gold-500/20 text-gold-400"
                    : "bg-zinc-800 text-zinc-400"
                } transition-all duration-300`}
              >
                {isImage ? (
                  <ImageIcon className="h-10 w-10" />
                ) : (
                  <Film className="h-10 w-10" />
                )}
              </div>
              <div>
                <p className="text-base font-semibold text-zinc-200">
                  {isDragActive
                    ? "Drop it here!"
                    : `Drag & drop your ${isImage ? "photo" : "video"} here`}
                </p>
                <p className="mt-1 text-sm text-zinc-500">
                  or{" "}
                  <span className="text-gold-400 underline underline-offset-2">
                    click to browse
                  </span>
                </p>
              </div>
              <div className="mt-1 flex flex-wrap justify-center gap-2">
                {(isImage
                  ? ["JPG", "PNG", "BMP", "TIFF", "WEBP"]
                  : ["MP4", "AVI", "MOV", "WEBM"]
                ).map((ext) => (
                  <span
                    key={ext}
                    className="rounded-md bg-zinc-800 px-2 py-0.5 text-xs font-mono text-zinc-400"
                  >
                    {ext}
                  </span>
                ))}
                <span className="rounded-md bg-zinc-800 px-2 py-0.5 text-xs text-zinc-500">
                  max {isImage ? "20MB" : "500MB"}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 flex items-center gap-2 rounded-lg bg-red-950/60 border border-red-800/40 px-4 py-2.5 text-sm text-red-300"
          >
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
