"""Evaluate the trained flood model on an aligned cyclone scene."""

from argparse import ArgumentParser
from pathlib import Path
import json

import numpy as np
import rasterio
import torch

from model import load_checkpoint


def normalise(features, mean, std):
    mean = np.asarray(mean, dtype=np.float32).reshape(-1, 1, 1)
    std = np.asarray(std, dtype=np.float32).reshape(-1, 1, 1)
    return (features - mean) / (std + 1e-6)


def predict_scene(model, stack, mean, std, threshold, device, tile_size):
    _, height, width = stack.shape
    prediction = np.zeros((height, width), dtype=np.uint8)

    for y0 in range(0, height, tile_size):
        for x0 in range(0, width, tile_size):
            y1 = min(y0 + tile_size, height)
            x1 = min(x0 + tile_size, width)
            tile = stack[:, y0:y1, x0:x1]
            tile_height, tile_width = tile.shape[1:]
            padded = np.zeros((4, tile_size, tile_size), dtype=np.float32)
            padded[:, :tile_height, :tile_width] = tile

            tensor = torch.from_numpy(normalise(padded, mean, std)).unsqueeze(0).to(device)
            with torch.no_grad():
                probability = torch.sigmoid(model(tensor)).squeeze().cpu().numpy()
            prediction[y0:y1, x0:x1] = (
                probability[:tile_height, :tile_width] > threshold
            ).astype(np.uint8)

    return prediction


def calculate_metrics(prediction, reference, valid):
    predicted = prediction[valid].astype(bool)
    observed = reference[valid].astype(bool)
    true_positive = np.count_nonzero(predicted & observed)
    false_positive = np.count_nonzero(predicted & ~observed)
    false_negative = np.count_nonzero(~predicted & observed)
    true_negative = np.count_nonzero(~predicted & ~observed)
    union = true_positive + false_positive + false_negative
    denominator = 2 * true_positive + false_positive + false_negative

    return {
        "valid_pixels": int(valid.sum()),
        "true_positive": int(true_positive),
        "false_positive": int(false_positive),
        "false_negative": int(false_negative),
        "true_negative": int(true_negative),
        "iou": float(true_positive / union) if union else 1.0,
        "dice_f1": float(2 * true_positive / denominator) if denominator else 1.0,
        "precision": float(true_positive / (true_positive + false_positive))
        if true_positive + false_positive
        else 0.0,
        "recall": float(true_positive / (true_positive + false_negative))
        if true_positive + false_negative
        else 0.0,
    }


def predict_patch(model, patch, mean, std, threshold, device, tile_size):
    """Predict one patch after padding it to the model input size."""
    channels, height, width = patch.shape
    padded = np.zeros((channels, tile_size, tile_size), dtype=np.float32)
    padded[:, :height, :width] = patch
    tensor = torch.from_numpy(normalise(padded, mean, std)).unsqueeze(0).to(device)
    with torch.no_grad():
        probability = torch.sigmoid(model(tensor)).squeeze().cpu().numpy()
    return (probability[:height, :width] > threshold).astype(np.uint8)


def aggregate_patch_metrics(
    model, stack, reference, mean, std, threshold, device, tile_size
):
    """Evaluate every non-overlapping tile and return macro and micro metrics."""
    _, height, width = stack.shape
    patch_metrics = []
    for y0 in range(0, height, tile_size):
        for x0 in range(0, width, tile_size):
            y1 = min(y0 + tile_size, height)
            x1 = min(x0 + tile_size, width)
            input_patch = stack[:, y0:y1, x0:x1]
            valid = np.isfinite(input_patch).all(axis=0)
            valid &= np.isfinite(reference[y0:y1, x0:x1])
            if not valid.any():
                continue
            filled = np.where(
                np.isfinite(input_patch),
                input_patch,
                np.asarray(mean, dtype=np.float32)[:, None, None],
            )
            prediction = predict_patch(
                model, filled, mean, std, threshold, device, tile_size
            )
            metrics = calculate_metrics(
                prediction, reference[y0:y1, x0:x1] > 0.5, valid
            )
            metrics.update({"row": y0, "column": x0})
            patch_metrics.append(metrics)

    if not patch_metrics:
        raise ValueError("The stack and reference contain no jointly valid pixels")

    metric_names = ("iou", "dice_f1", "precision", "recall")
    macro = {
        name: float(np.mean([metrics[name] for metrics in patch_metrics]))
        for name in metric_names
    }
    totals = {
        name: int(sum(metrics[name] for metrics in patch_metrics))
        for name in (
            "valid_pixels",
            "true_positive",
            "false_positive",
            "false_negative",
            "true_negative",
        )
    }
    micro = {
        "valid_pixels": totals["valid_pixels"],
        "true_positive": totals["true_positive"],
        "false_positive": totals["false_positive"],
        "false_negative": totals["false_negative"],
        "true_negative": totals["true_negative"],
    }
    union = totals["true_positive"] + totals["false_positive"] + totals["false_negative"]
    denominator = 2 * totals["true_positive"] + totals["false_positive"] + totals["false_negative"]
    micro.update(
        {
            "iou": float(totals["true_positive"] / union) if union else 1.0,
            "dice_f1": float(2 * totals["true_positive"] / denominator)
            if denominator
            else 1.0,
            "precision": float(
                totals["true_positive"]
                / (totals["true_positive"] + totals["false_positive"])
            )
            if totals["true_positive"] + totals["false_positive"]
            else 0.0,
            "recall": float(
                totals["true_positive"]
                / (totals["true_positive"] + totals["false_negative"])
            )
            if totals["true_positive"] + totals["false_negative"]
            else 0.0,
        }
    )
    return {
        "patch_count": len(patch_metrics),
        "macro_mean": macro,
        "micro_overall": micro,
        "patches": patch_metrics,
    }


def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--stack", type=Path, required=True, help="Four- or six-band input GeoTIFF")
    parser.add_argument("--reference", type=Path, help="Aligned binary flood-mask GeoTIFF")
    parser.add_argument("--checkpoint", type=Path, default=Path("models/checkpoints/unet_best.pt"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/evaluation"))
    parser.add_argument("--threshold", type=float, help="Override the checkpoint threshold")
    parser.add_argument("--tile-size", type=int, default=256)
    parser.add_argument(
        "--aggregate-patches",
        action="store_true",
        help="Report mean and overall metrics across every valid tile",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.tile_size <= 0:
        raise ValueError("--tile-size must be positive")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, checkpoint = load_checkpoint(str(args.checkpoint), device=device)
    threshold = (
        float(args.threshold)
        if args.threshold is not None
        else float(checkpoint.get("threshold", 0.5))
    )
    mean = checkpoint["normalisation"]["mean"]
    std = checkpoint["normalisation"]["std"]

    with rasterio.open(args.stack) as source:
        if source.count < 4:
            raise ValueError("The input stack must contain at least four bands")
        stack = source.read([1, 2, 3, 4]).astype(np.float32)
        profile = source.profile.copy()
        source_valid = np.isfinite(stack).all(axis=0)
        prediction = predict_scene(
            model, np.nan_to_num(stack, nan=0.0, posinf=0.0, neginf=0.0),
            mean, std, threshold, device, args.tile_size
        )
        profile.update(count=1, dtype="uint8", nodata=0, compress="lzw")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = args.output_dir / f"{args.stack.stem}_prediction.tif"
    with rasterio.open(prediction_path, "w", **profile) as destination:
        destination.write(prediction, 1)

    result = {
        "stack": str(args.stack),
        "checkpoint": str(args.checkpoint),
        "device": device,
        "threshold": threshold,
        "prediction": str(prediction_path),
    }
    if args.reference:
        with rasterio.open(args.reference) as reference_source:
            reference = reference_source.read(1)
            reference_valid = np.isfinite(reference)
            if reference.shape != prediction.shape:
                raise ValueError("Reference mask must have the same rows and columns as the stack")
            if reference_source.crs != profile["crs"] or reference_source.transform != profile["transform"]:
                raise ValueError("Reference mask must have the same CRS and transform as the stack")
        result["metrics"] = calculate_metrics(
            prediction, reference > 0.5, source_valid & reference_valid
        )
        if args.aggregate_patches:
            result["aggregated_metrics"] = aggregate_patch_metrics(
                model,
                stack,
                reference,
                mean,
                std,
                threshold,
                device,
                args.tile_size,
            )

    metrics_path = args.output_dir / f"{args.stack.stem}_metrics.json"
    metrics_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
