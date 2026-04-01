import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export default function ProcessingProgress({ status, progress, message }) {
  const isProcessing = status === "processing" || status === "queued";
  const isFailed = status === "failed";

  const barColor = isFailed
    ? "bg-red-500"
    : progress === 100
    ? "bg-green-500"
    : "bg-gradient-to-r from-sepia-500 via-gold-400 to-amber-300";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`rounded-2xl border p-6 ${
        isFailed
          ? "border-red-800/40 bg-red-950/30"
          : "dark:border-zinc-700/50 border-zinc-200 dark:bg-zinc-900/70 bg-white/80"
      }`}
    >
      {/* Header */}
      <div className="mb-4 flex items-center gap-3">
        {isProcessing && (
          <Loader2 className="h-5 w-5 animate-spin text-gold-400" />
        )}
        {isFailed && (
          <span className="text-lg">⚠️</span>
        )}
        {status === "completed" && (
          <span className="text-lg">✅</span>
        )}
        <div>
          <p className="font-semibold text-zinc-100">
            {status === "queued" && "Queued…"}
            {status === "processing" && "Colorizing…"}
            {status === "completed" && "Done!"}
            {status === "failed" && "Processing failed"}
          </p>
          <p className="mt-0.5 text-sm dark:text-zinc-400 text-zinc-500">{message}</p>
        </div>
        <span className="ml-auto text-2xl font-bold tabular-nums text-gold-400">
          {progress}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-3 w-full overflow-hidden rounded-full dark:bg-zinc-800 bg-zinc-200">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ ease: "easeOut", duration: 0.4 }}
        />
      </div>

      {/* Shimmer when processing */}
      {isProcessing && (
        <div className="mt-4 space-y-2">
          {[80, 60, 40].map((w) => (
            <div
              key={w}
              className="shimmer h-2.5 rounded-full bg-zinc-800"
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}
