import { motion } from "framer-motion";

export default function VideoResult({ originalUrl, colorizedUrl }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/70 shadow-2xl"
    >
      <div className="border-b border-zinc-800 bg-zinc-900/80 px-4 py-2 text-center">
        <span className="text-xs font-semibold uppercase tracking-widest text-gold-400">
          Side-by-side comparison
        </span>
      </div>

      <div className="grid grid-cols-1 gap-0 sm:grid-cols-2">
        {/* Original */}
        <div className="border-b border-zinc-800 sm:border-b-0 sm:border-r">
          <div className="bg-zinc-800/50 px-3 py-1.5 text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Original B&amp;W
            </p>
          </div>
          <video
            src={originalUrl}
            className="w-full"
            controls
            muted
            style={{ filter: "grayscale(100%)" }}
          />
        </div>

        {/* Colorized */}
        <div>
          <div className="bg-zinc-800/50 px-3 py-1.5 text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-gold-400">
              Colorized ✨
            </p>
          </div>
          <video
            src={colorizedUrl}
            className="w-full"
            controls
            muted
          />
        </div>
      </div>
    </motion.div>
  );
}
