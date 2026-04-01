import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

/**
 * Interactive before/after image comparison slider.
 * Drag (or touch) the divider to compare the original B&W with the colorized version.
 */
export default function ComparisonSlider({ before, after }) {
  const [position, setPosition] = useState(50); // percentage
  const containerRef = useRef(null);
  const dragging = useRef(false);

  const clamp = (v) => Math.max(0, Math.min(100, v));

  const updateFromEvent = (clientX) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setPosition(clamp(((clientX - rect.left) / rect.width) * 100));
  };

  // Mouse
  const onMouseDown = (e) => {
    e.preventDefault();
    dragging.current = true;
  };
  useEffect(() => {
    const onMove = (e) => dragging.current && updateFromEvent(e.clientX);
    const onUp = () => { dragging.current = false; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  // Touch
  const onTouchStart = (e) => {
    dragging.current = true;
    updateFromEvent(e.touches[0].clientX);
  };
  useEffect(() => {
    const onMove = (e) => dragging.current && updateFromEvent(e.touches[0].clientX);
    const onEnd = () => { dragging.current = false; };
    window.addEventListener("touchmove", onMove, { passive: true });
    window.addEventListener("touchend", onEnd);
    return () => {
      window.removeEventListener("touchmove", onMove);
      window.removeEventListener("touchend", onEnd);
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full overflow-hidden rounded-2xl shadow-2xl"
    >
      {/* Labels */}
      <div className="flex justify-between px-4 py-2 bg-zinc-900/80 backdrop-blur-sm border-b border-zinc-800">
        <span className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
          Original B&amp;W
        </span>
        <span className="text-xs font-semibold uppercase tracking-widest text-gold-400">
          Colorized ✨
        </span>
      </div>

      {/* Slider */}
      <div
        ref={containerRef}
        className="comparison-container select-none"
        onMouseDown={(e) => updateFromEvent(e.clientX)}
        onTouchStart={onTouchStart}
        style={{ cursor: "ew-resize" }}
      >
        {/* After (colorized) — bottom layer, full width */}
        <img
          src={after}
          alt="Colorized"
          className="block w-full object-cover"
          draggable={false}
        />

        {/* Before (B&W) — clipped overlay */}
        <div
          className="comparison-overlay"
          style={{ width: `${position}%` }}
        >
          <img
            src={before}
            alt="Original"
            className="block object-cover"
            draggable={false}
            style={{ width: containerRef.current?.offsetWidth ?? "100%" }}
          />
        </div>

        {/* Divider handle */}
        <div
          className="comparison-handle"
          style={{ left: `${position}%` }}
          onMouseDown={onMouseDown}
        >
          <div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10
                        rounded-full bg-white shadow-xl flex items-center justify-center z-20"
          >
            <svg
              className="w-5 h-5 text-zinc-700"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8 9l-3 3 3 3M16 9l3 3-3 3"
              />
            </svg>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
