"""
Pre-download the colorization model weights from AWS S3.
Run this once before starting the server to avoid a cold-start delay.
"""
import sys
from colorizer import Colorizer

print("=== OldWorldColored — model weight pre-download ===\n")
try:
    _ = Colorizer()
    print("\n=== Model ready. ===")
except Exception as exc:
    print(f"\nWARNING: {exc}", file=sys.stderr)
    print("The model will be downloaded automatically on the first request.", file=sys.stderr)
