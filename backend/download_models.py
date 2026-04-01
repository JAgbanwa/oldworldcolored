"""
Download the pre-trained colorization model weights.
Source: Zhang et al. (2016) "Colorful Image Colorization" - ECCV 2016
"""
import os
import urllib.request
import sys

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

MODEL_FILES = {
    "colorization_deploy_v2.prototxt": (
        "https://raw.githubusercontent.com/richzhang/colorization/caffe/"
        "colorization/models/colorization_deploy_v2.prototxt"
    ),
    "pts_in_hull.npy": (
        "https://raw.githubusercontent.com/richzhang/colorization/caffe/"
        "colorization/resources/pts_in_hull.npy"
    ),
    "colorization_release_v2.caffemodel": (
        "http://eecs.berkeley.edu/~rich.zhang/projects/2016_colorization/"
        "files/demo_v2/colorization_release_v2.caffemodel"
    ),
}

CAFFEMODEL_FALLBACK = (
    "https://huggingface.co/datasets/hf-internal-testing/fixtures_porting/"
    "resolve/main/colorization_release_v2.caffemodel"
)


def download_file(url: str, dest: str, desc: str) -> bool:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"  Downloading {desc}...", flush=True)
    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                pct = min(100, int(count * block_size * 100 / total_size))
                print(f"\r    {pct}%  ", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook)
        print(f"\r    Done.        ")
        return True
    except Exception as e:
        print(f"\r    Failed: {e}")
        if os.path.exists(dest):
            os.remove(dest)
        return False


def download_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("=== Downloading colorization model files ===\n")

    for filename, url in MODEL_FILES.items():
        dest = os.path.join(MODELS_DIR, filename)
        if os.path.exists(dest):
            print(f"  ✓ {filename} already downloaded.")
            continue

        success = download_file(url, dest, filename)

        # Caffemodel has a fallback URL
        if not success and filename == "colorization_release_v2.caffemodel":
            print(f"  Trying fallback URL for caffemodel...")
            success = download_file(CAFFEMODEL_FALLBACK, dest, filename)

        if not success:
            print(
                f"\n  ERROR: Could not download {filename}.\n"
                "  Please download it manually:\n"
                f"    URL: {url}\n"
                f"    Destination: {dest}\n"
            )
            sys.exit(1)

    print("\n=== All model files ready. ===")


if __name__ == "__main__":
    download_models()
