"""
Pre-download the colorization model weights.
The `colorizers` package fetches the model (~56 MB) from AWS S3 and caches
it under ~/.cache/torch/hub/checkpoints/ automatically.
"""
import sys


def download_models():
    print("=== Downloading colorization model weights (AWS S3) ===\n")
    try:
        from colorizers import eccv16
        print("  Loading ECCV16 model (downloads on first run)...")
        _ = eccv16(pretrained=True)
        print("\n=== Model ready. ===")
    except Exception as e:
        print(f"\n  WARNING: {e}", file=sys.stderr)
        print("  The model will be re-attempted when the server starts.", file=sys.stderr)


if __name__ == "__main__":
    download_models()
