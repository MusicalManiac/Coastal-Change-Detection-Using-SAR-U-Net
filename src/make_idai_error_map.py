"""Create a slide-ready hit/false-alarm/miss map for the Idai evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.windows import Window


EXPECTED = {
    "true_positive": 502_610,
    "false_positive": 364_327,
    "false_negative": 507_957,
    "true_negative": 10_852_084,
    "iou": 0.366,
    "f1": 0.535,
    "precision": 0.580,
    "recall": 0.497,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", type=Path, required=True)
    parser.add_argument("--prediction", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--underlay",
        action="store_true",
        help="Draw the classes semi-transparently over post-event VV.",
    )
    parser.add_argument(
        "--max-display-pixels",
        type=int,
        default=2_000_000,
        help="Approximate maximum number of pixels in the cropped display.",
    )
    parser.add_argument(
        "--callouts",
        nargs=3,
        action="append",
        metavar=("X", "Y", "TEXT"),
        help="Optional map callout; repeat up to twice.",
    )
    return parser.parse_args()


def validate_grids(stack, prediction, reference) -> None:
    expected = (stack.width, stack.height, stack.crs, stack.transform)
    for name, source in (("prediction", prediction), ("reference", reference)):
        actual = (source.width, source.height, source.crs, source.transform)
        if actual != expected:
            raise ValueError(
                f"{name} is not on the stack grid: dimensions, CRS, or transform differ"
            )


def valid_bounds(stack, reference, block_size: int = 1024) -> tuple[int, int, int, int]:
    min_row, min_col = stack.height, stack.width
    max_row = max_col = -1
    for row in range(0, stack.height, block_size):
        for col in range(0, stack.width, block_size):
            height = min(block_size, stack.height - row)
            width = min(block_size, stack.width - col)
            window = Window(col, row, width, height)
            bands = stack.read([1, 2, 3, 4], window=window, masked=False)
            ref = reference.read(1, window=window, masked=False)
            valid = np.isfinite(bands).all(axis=0) & np.isfinite(ref)
            if not valid.any():
                continue
            rows, cols = np.where(valid)
            min_row = min(min_row, row + int(rows.min()))
            max_row = max(max_row, row + int(rows.max()))
            min_col = min(min_col, col + int(cols.min()))
            max_col = max(max_col, col + int(cols.max()))
    if max_row < 0:
        raise ValueError("The stack and reference contain no jointly valid pixels")
    return min_row, min_col, max_row + 1, max_col + 1


def display_shape(height: int, width: int, max_pixels: int) -> tuple[int, int]:
    scale = min(1.0, np.sqrt(max_pixels / float(height * width)))
    return max(1, int(round(height * scale))), max(1, int(round(width * scale)))


def priority_reduce(
    classes: np.ndarray, out_height: int, out_width: int
) -> np.ndarray:
    """Downsample classes while prioritising errors and hits over TN."""
    height, width = classes.shape
    row_edges = np.linspace(0, height, out_height + 1, dtype=int)
    col_edges = np.linspace(0, width, out_width + 1, dtype=int)
    priority = (3, 2, 1, 0)
    result = np.full((out_height, out_width), 0, dtype=np.uint8)
    for out_row in range(out_height):
        for out_col in range(out_width):
            block = classes[
                row_edges[out_row] : row_edges[out_row + 1],
                col_edges[out_col] : col_edges[out_col + 1],
            ]
            if block.size:
                present = set(np.unique(block).tolist())
                result[out_row, out_col] = next(
                    value for value in priority if value in present
                )
    return result


def load_cropped(
    stack, prediction, reference, bounds, shape
) -> tuple[np.ndarray, np.ndarray, np.ndarray, rasterio.Affine]:
    min_row, min_col, max_row, max_col = bounds
    window = Window(min_col, min_row, max_col - min_col, max_row - min_row)
    bands = stack.read([1, 2, 3, 4], window=window, out_shape=(4, *shape))
    pred = prediction.read(1, window=window, out_shape=shape)
    ref = reference.read(1, window=window, out_shape=shape)
    transform = rasterio.windows.transform(window, stack.transform) * Affine.scale(
        window.width / shape[1], window.height / shape[0]
    )
    return bands, pred, ref, transform


def metrics_from_counts(
    true_positive: int,
    false_positive: int,
    false_negative: int,
    true_negative: int,
) -> dict[str, float | int]:
    tp = true_positive
    fp = false_positive
    fn = false_negative
    tn = true_negative
    union = tp + fp + fn
    denominator = 2 * tp + fp + fn
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "iou": tp / union if union else 1.0,
        "f1": 2 * tp / denominator if denominator else 1.0,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
    }


def count_metrics(stack, prediction, reference, block_size: int = 1024):
    counts = {"true_positive": 0, "false_positive": 0, "false_negative": 0, "true_negative": 0}
    for row in range(0, stack.height, block_size):
        for col in range(0, stack.width, block_size):
            height = min(block_size, stack.height - row)
            width = min(block_size, stack.width - col)
            window = Window(col, row, width, height)
            bands = stack.read([1, 2, 3, 4], window=window, masked=False)
            pred = prediction.read(1, window=window, masked=False)
            ref = reference.read(1, window=window, masked=False)
            valid = np.isfinite(bands).all(axis=0) & np.isfinite(ref)
            predicted = np.isfinite(pred) & (pred > 0)
            observed = np.isfinite(ref) & (ref > 0.5)
            counts["true_positive"] += int(np.count_nonzero(valid & predicted & observed))
            counts["false_positive"] += int(np.count_nonzero(valid & predicted & ~observed))
            counts["false_negative"] += int(np.count_nonzero(valid & ~predicted & observed))
            counts["true_negative"] += int(np.count_nonzero(valid & ~predicted & ~observed))
    return metrics_from_counts(**counts)


def print_metrics(metrics: dict[str, float | int]) -> None:
    print("Figure confusion counts:")
    for key in ("true_positive", "false_positive", "false_negative", "true_negative"):
        print(f"  {key}: {metrics[key]:,}")
    print("Figure pooled metrics:")
    for key in ("iou", "f1", "precision", "recall"):
        print(f"  {key}: {metrics[key]:.3f}")
    mismatches = []
    for key, expected in EXPECTED.items():
        actual = float(metrics[key])
        if key in {"iou", "f1", "precision", "recall"}:
            matches = abs(actual - expected) <= 0.0005
        else:
            matches = actual == expected
        if not matches:
            mismatches.append(f"{key}: figure={actual}, reported={expected}")
    if mismatches:
        print("WARNING: these values do not match the requested reported run:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        print(
            "No values were adjusted. The figure uses the supplied raster files; "
            "the reported counts likely came from a different prediction/reference "
            "pair, evaluator run, or valid-pixel mask."
        )
    else:
        print("Confirmed: figure metrics match the reported run.")


def add_scale_bar(ax, transform, latitude: float) -> None:
    from matplotlib.lines import Line2D

    metres = 10_000
    map_width = metres / np.cos(np.deg2rad(latitude))
    print(
        f"Scale bar: {map_width:.2f} map units represents "
        f"{metres / 1000:.1f} km ground distance at latitude {latitude:.2f}°."
    )
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    x0 = x_min + 0.05 * (x_max - x_min)
    y0 = y_min + 0.06 * (y_max - y_min)
    ax.add_line(Line2D([x0, x0 + map_width], [y0, y0], color="black", linewidth=3))
    ax.text(
        x0 + map_width / 2,
        y0 + 0.02 * (y_max - y_min),
        "10 km",
        ha="center",
        va="bottom",
        fontsize=12,
        color="black",
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )


def add_north_arrow(ax) -> None:
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    x = x_min + 0.94 * (x_max - x_min)
    y = y_min + 0.82 * (y_max - y_min)
    ax.annotate(
        "N",
        xy=(x, y + 0.09 * (y_max - y_min)),
        xytext=(x, y),
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "color": "black", "lw": 2},
    )


def make_figure(
    classes: np.ndarray,
    underlay: np.ndarray | None,
    transform,
    crs,
    output: Path,
    metrics: dict[str, float | int],
    callouts: list[tuple[float, float, str]],
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    colours = ["#d9d9d9", "#cc79a7", "#e69f00", "#0072b2"]
    labels = [
        "Correctly not flagged (radar shown)",
        "Miss",
        "False alarm",
        "Hit",
    ]
    masked_classes = np.ma.masked_where(classes == 255, classes)
    extent = (
        transform.c,
        transform.c + transform.a * classes.shape[1],
        transform.f + transform.e * classes.shape[0],
        transform.f,
    )
    fig = plt.figure(figsize=(16, 9), dpi=300)
    ax = fig.add_axes([0.04, 0.16, 0.69, 0.72])
    if underlay is not None:
        ax.imshow(
            underlay,
            cmap="gray",
            vmin=np.nanpercentile(underlay, 2),
            vmax=np.nanpercentile(underlay, 98),
            extent=extent,
            origin="upper",
        )
        alpha = np.where(classes == 0, 0.15, np.where(classes == 255, 0, 0.72))
        ax.imshow(
            np.ma.masked_where(classes == 255, classes),
            cmap=ListedColormap(colours),
            vmin=0,
            vmax=3,
            extent=extent,
            origin="upper",
            alpha=alpha,
            interpolation="nearest",
        )
    else:
        ax.imshow(
            masked_classes,
            cmap=ListedColormap(colours),
            vmin=0,
            vmax=3,
            extent=extent,
            origin="upper",
            interpolation="nearest",
        )
    ax.set_axis_off()
    handles = [
        Patch(facecolor=colours[i], edgecolor="none", label=labels[i])
        for i in range(4)
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=11, framealpha=0.95)
    add_scale_bar(ax, transform, -19.84)
    add_north_arrow(ax)
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    for x, y, text in callouts:
        ax.annotate(
            text,
            xy=(x, y),
            xytext=(x + 0.04 * (x_max - x_min), y + 0.05 * (y_max - y_min)),
            fontsize=12,
            color="#0072b2",
            bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "#0072b2"},
            arrowprops={"arrowstyle": "-|>", "color": "#0072b2", "lw": 1.5},
        )
    metric_panel = fig.add_axes([0.75, 0.22, 0.24, 0.58])
    metric_panel.set_axis_off()
    metric_panel.text(
        0.0, 0.98, "Pooled performance", fontsize=20, fontweight="bold", va="top"
    )
    metric_items = [
        ("IoU", metrics["iou"], "#0072b2"),
        ("F1", metrics["f1"], "#cc79a7"),
        ("Precision", metrics["precision"], "#e69f00"),
        ("Recall", metrics["recall"], "#0072b2"),
    ]
    y = 0.80
    for label, value, colour in metric_items:
        metric_panel.text(
            0.0, y, label, fontsize=17, color=colour, fontweight="bold", va="top"
        )
        metric_panel.text(
            0.98, y, f"{value:.2f}", fontsize=25, fontweight="bold",
            ha="right", va="top", color="black"
        )
        y -= 0.16
    metric_panel.text(
        0.0,
        0.12,
        "We found about half of the mapped flooding;\nabout 58% of what we flagged\nwas in the reference.",
        fontsize=12,
        va="top",
        linespacing=1.35,
    )
    fig.text(
        0.04,
        0.055,
        "Reference: WFP/HDX detected-water extent (coarse ~95 m, compiled 12-21 Mar; "
        "may include rivers and coastal water). Threshold 0.5.",
        fontsize=15,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, facecolor="white")
    if output.suffix.lower() != ".svg":
        fig.savefig(output.with_suffix(".svg"), facecolor="white")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    if args.max_display_pixels <= 0:
        raise ValueError("--max-display-pixels must be positive")
    if args.callouts and len(args.callouts) > 2:
        raise ValueError("--callouts may be supplied at most twice")
    callouts = []
    for callout in args.callouts or []:
        try:
            callouts.append((float(callout[0]), float(callout[1]), callout[2]))
        except ValueError as exc:
            raise ValueError("--callouts requires numeric X and Y coordinates") from exc
    with rasterio.open(args.stack) as stack, rasterio.open(
        args.prediction
    ) as prediction, rasterio.open(args.reference) as reference:
        if stack.count < 4:
            raise ValueError("--stack must contain at least four bands")
        validate_grids(stack, prediction, reference)
        bounds = valid_bounds(stack, reference)
        height = bounds[2] - bounds[0]
        width = bounds[3] - bounds[1]
        shape = display_shape(height, width, args.max_display_pixels)
        bands, pred, ref, transform = load_cropped(
            stack, prediction, reference, bounds, shape
        )
        valid = np.isfinite(bands).all(axis=0) & np.isfinite(ref)
        predicted = np.isfinite(pred) & (pred > 0)
        observed = np.isfinite(ref) & (ref > 0.5)
        classes = np.full(shape, 255, dtype=np.uint8)
        classes[valid & ~predicted & ~observed] = 0
        classes[valid & ~predicted & observed] = 1
        classes[valid & predicted & ~observed] = 2
        classes[valid & predicted & observed] = 3
        metrics = count_metrics(stack, prediction, reference)
        print_metrics(metrics)
        underlay = bands[2] if args.underlay else None
        make_figure(
            classes,
            underlay,
            transform,
            stack.crs,
            args.output,
            metrics,
            callouts,
        )
        print(f"Wrote PNG: {args.output}")
        if args.output.suffix.lower() != ".svg":
            print(f"Wrote SVG: {args.output.with_suffix('.svg')}")


if __name__ == "__main__":
    main()
