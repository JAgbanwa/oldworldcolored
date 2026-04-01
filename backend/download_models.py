"""
Pre-download model weights so the first request isn't slow.
  • Colorization model  – Zhang et al. ECCV 2016        (~56 MB, AWS S3)
  • Super-resolution    – Real-ESRGAN x4plus 6-block    (~17 MB, GitHub releases)
"""
import sys
from colorizer import Colorizer
from upscaler import Upscaler

print("=== OldWorldColored — model weight pre-download ===\n")

try:
    _ = Colorizer()
    print("[colorizer] ready ✓")
except Exception as exc:
    print(f"[colorizer] WARNING: {exc}", file=sys.stderr)
    print("  → colorizer will be downloaded on first request.", file=sys.stderr)

try:
    _ = Upscaler()
    print("[upscaler]  ready ✓")
except Exception as exc:
    print(f"[upscaler]  WARNING: {exc}", file=sys.stderr)
    print("  → upscaler will be downloaded on first SR request.", file=sys.stderr)

print("\n=== All models ready. ===")

