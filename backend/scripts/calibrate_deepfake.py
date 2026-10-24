"""
Deepfake detector calibration script.

Runs the deployed EfficientNet-B3 detector over two folders of labeled
images and computes the decision threshold + softmax temperature that best
separate REAL from FAKE. Writes models/deepfake_calibration.json, which the
detector reads per-prediction (no restart needed afterwards).

Usage (inside the backend container):
    docker exec truthlens_backend python scripts/calibrate_deepfake.py \
        --real-dir /app/data/calibration/real \
        --fake-dir /app/data/calibration/fake

    # Preview only, writes nothing:
    docker exec truthlens_backend python scripts/calibrate_deepfake.py \
        --real-dir ... --fake-dir ... --dry-run

Prepare samples:
    data/calibration/real/  - images you know are authentic (camera photos,
                              screenshots of real media, etc.)
    data/calibration/fake/  - images you know are AI-generated / manipulated

~10-20 images per class is enough for a usable cut; 50+ per class for a
trustworthy temperature fit.
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import List, Tuple

import torch
from PIL import Image

# Allow running as a plain script inside the container (/app is cwd)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.deepfake import get_deepfake_detector, DeepfakeDetector

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_images(directory: Path) -> List[Path]:
    """Gather supported image files from a directory (non-recursive)."""
    if not directory or not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir()
                  if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)


def balanced_accuracy(scores: List[float], labels: List[int], threshold: float) -> float:
    """
    BALANCED accuracy at a given fake-probability threshold.
    labels: 1 = fake, 0 = real.
    """
    real_correct = sum(1 for s, y in zip(scores, labels) if (y == 0) == (s < threshold))
    fake_correct = sum(1 for s, y in zip(scores, labels) if (y == 1) == (s >= threshold))
    n_real = max(1, sum(1 for y in labels if y == 0))
    n_fake = max(1, sum(1 for y in labels if y == 1))
    return (real_correct / n_real + fake_correct / n_fake) / 2


def fit_temperature(logits_pos: List[Tuple[float, float]], labels: List[int]) -> float:
    """
    Coarse temperature search minimizing NLL of labels given fake/real probs.
    logits_pos: list of (real_prob, fake_prob) BEFORE calibration (T=1).
    """
    best_t, best_nll = 1.0, float("inf")
    for t in [0.4, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]:
        nll = 0.0
        for (real_prob, fake_prob), y in zip(logits_pos, labels):
            # Recover pre-temperature mix, re-sharpen by 1/t
            mix = [(real_prob) ** (1.0 / t), (fake_prob) ** (1.0 / t)]
            z = sum(mix)
            p_fake = (mix[1] / z) if z > 0 else 0.5
            p_fake = min(1 - 1e-6, max(1e-6, p_fake))
            nll -= math.log(p_fake) if y == 1 else math.log(1 - p_fake)
        if nll < best_nll:
            best_nll, best_t = nll, t
    return round(best_t, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate deepfake detector threshold/temperature")
    parser.add_argument("--real-dir", required=True, help="Folder of known-authentic images")
    parser.add_argument("--fake-dir", required=True, help="Folder of known-fake images")
    parser.add_argument("--dry-run", action="store_true", help="Report only; don't write calibration file")
    args = parser.parse_args()

    real_paths = collect_images(Path(args.real_dir))
    fake_paths = collect_images(Path(args.fake_dir))
    if not real_paths or not fake_paths:
        print(f"Need images in BOTH folders (real: {len(real_paths)}, fake: {len(fake_paths)}).")
        return 2

    detector = get_deepfake_detector()

    scores: List[float] = []
    labels: List[int] = []          # 1 = fake, 0 = real
    raw_pairs: List[Tuple[float, float]] = []
    failures: List[str] = []

    paths_labels = [(p, 0) for p in real_paths] + [(p, 1) for p in fake_paths]
    for path, label in paths_labels:
        try:
            image = Image.open(path).convert("RGB")
            tensor = detector.transform(image).unsqueeze(0).to(detector.device)
            with torch.no_grad():
                probs = torch.softmax(detector.model(tensor), dim=1)[0]
            real_prob, fake_prob = probs[0].item(), probs[1].item()
        except Exception as exc:
            failures.append(f"{path.name}: {exc}")
            continue
        scores.append(fake_prob)
        labels.append(label)
        raw_pairs.append((real_prob, fake_prob))

    if failures:
        print(f"Skipped {len(failures)} unreadable images:")
        for f in failures[:5]:
            print(f"  {f}")

    n_real, n_fake = labels.count(0), labels.count(1)
    if not n_real or not n_fake:
        print("No usable probabilities collected.")
        return 2

    print(f"\nSamples: {n_real} real, {n_fake} fake")
    print("\n--- Linear-scan (threshold -> balanced accuracy) ---")
    best_threshold, best_score = 0.5, 0.0
    for t in [x / 100 for x in range(30, 71, 2)]:
        acc = balanced_accuracy(scores, labels, t)
        print(f"  {t:.2f}  ->  {acc * 100:6.1f}%")
        if acc > best_score:
            best_score, best_threshold = acc, t

    base_acc = balanced_accuracy(scores, labels, 0.5)
    temperature = 1.0
    if n_real + n_fake >= 20:
        temperature = fit_temperature(raw_pairs, labels)

    print(f"\nCurrent verdict cut (0.50): {base_acc * 100:.1f}% balanced accuracy")
    print(f"Recommended threshold:      {best_threshold:.2f} -> {best_score * 100:.1f}% balanced accuracy")
    print(f"Fitted temperature:         {temperature}")

    if args.dry_run:
        print("\n[dry-run] no calibration file written")
        return 0

    out_path = DeepfakeDetector.CALIBRATION_FILE
    payload = {
        "threshold": best_threshold,
        "temperature": temperature,
        "updated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "samples": {"real": n_real, "fake": n_fake},
        "balanced_accuracy_at_threshold": round(best_score, 4),
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print("Takes effect on the next prediction (no restart needed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
