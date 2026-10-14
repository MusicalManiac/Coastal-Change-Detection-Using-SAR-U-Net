"""
Local Streamlit demo UI for the SAR flood-detection model.

Run:
    streamlit run src/app.py

Loads the full GeoTIFF, lets you scroll a region, runs Sebastian's trained
U-Net (smp, ResNet34 encoder) on it, and shows pre/post SAR + prediction
side by side.
"""

from pathlib import Path

import numpy as np
import rasterio
import streamlit as st
import torch
from rasterio.io import MemoryFile

from evaluate_model import aggregate_patch_metrics
from model import load_checkpoint

st.set_page_config(layout="wide", page_title="SAR Flood Detection Demo")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOTIFF_PATH = PROJECT_ROOT / "data" / "raw" / "CycloneGabrielle_HawkesBay_S1_Stack_v2.tif"
CHECKPOINT_PATH = PROJECT_ROOT / "models" / "checkpoints" / "unet_best.pt"
PATCH_SIZE = 256


@st.cache_resource
def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, checkpoint = load_checkpoint(CHECKPOINT_PATH, device=device)
    return model, checkpoint, device


@st.cache_data
def load_raster(path):
    with rasterio.open(path) as src:
        data = src.read()
        profile = src.profile.copy()
    return data, profile


def load_uploaded_raster(uploaded_file):
    with MemoryFile(uploaded_file.getvalue()) as memory_file:
        with memory_file.open() as source:
            return source.read(), source.profile.copy()


def normalise(patch, mean, std):
    mean = np.array(mean, dtype=np.float32).reshape(-1, 1, 1)
    std = np.array(std, dtype=np.float32).reshape(-1, 1, 1)
    return (patch - mean) / (std + 1e-6)


def to_display(band, vmin=-25, vmax=0):
    clipped = np.nan_to_num(band, nan=vmin, posinf=vmax, neginf=vmin)
    clipped = np.clip(clipped, vmin, vmax)
    return ((clipped - vmin) / (vmax - vmin) * 255).astype(np.uint8)


def find_best_patch(data, patch_size):
    valid = np.isfinite(data[:4]).all(axis=0)
    height, width = valid.shape
    best_score = -1.0
    best_position = (0, 0)
    for y0 in range(0, max(height - patch_size + 1, 1), patch_size):
        for x0 in range(0, max(width - patch_size + 1, 1), patch_size):
            score = float(valid[y0 : y0 + patch_size, x0 : x0 + patch_size].mean())
            if score > best_score:
                best_score = score
                best_position = (y0, x0)
    return best_position, best_score


st.title("SAR Coastal Flood Detection")
st.caption(
    "Change-detection U-Net (ResNet34 encoder): given a pre-event and post-event "
    "Sentinel-1 SAR pair, predicts which pixels flooded. Decision-support output, "
    "not a safety certification."
)

model, checkpoint, device = load_model()

mean = checkpoint["normalisation"]["mean"]
std = checkpoint["normalisation"]["std"]
input_bands = checkpoint["input_bands"]  # e.g. ['pre_vv', 'pre_vh', 'post_vv', 'post_vh']
threshold_default = checkpoint.get("threshold", 0.5)

st.sidebar.markdown(
    f"**Checkpoint:** epoch {checkpoint['epoch']}, val IoU {checkpoint['val_iou']:.3f}"
)
st.sidebar.header("Load cyclone data")
use_bundled = st.sidebar.checkbox("Use bundled Gabrielle example", value=False)
uploaded_scene = st.sidebar.file_uploader(
    "Upload cyclone input GeoTIFF",
    type=["tif", "tiff"],
    help=(
        "Upload four bands in order: pre-event VV, pre-event VH, post-event VV, "
        "post-event VH. A six-band Gabrielle-style file is also accepted."
    ),
    disabled=use_bundled,
)
uploaded_reference = st.sidebar.file_uploader(
    "Optional independent reference-mask GeoTIFF",
    type=["tif", "tiff"],
    help="Upload a binary mask on the exact same grid as the input GeoTIFF.",
    disabled=use_bundled,
)

if use_bundled:
    scene_path = GEOTIFF_PATH
    data, raster_profile = load_raster(str(scene_path))
    scene_label = "Bundled Cyclone Gabrielle example"
    reference_data = None
    reference_profile = None
else:
    if uploaded_scene is None:
        st.info(
            "Upload a cyclone GeoTIFF in the sidebar to start a live test. "
            "The file must contain four aligned bands: pre-event VV, pre-event VH, "
            "post-event VV, and post-event VH."
        )
        st.stop()
    data, raster_profile = load_uploaded_raster(uploaded_scene)
    scene_label = uploaded_scene.name
    reference_data = None
    reference_profile = None
    if uploaded_reference is not None:
        reference_data, reference_profile = load_uploaded_raster(uploaded_reference)

height, width = data.shape[1:]
if data.shape[0] < 4:
    st.error("The cyclone GeoTIFF must contain at least four bands.")
    st.stop()
if data.shape[0] > 6:
    st.error("The cyclone GeoTIFF must contain four or six bands.")
    st.stop()

has_reference = reference_data is not None
if has_reference:
    if reference_data.shape[0] != 1:
        st.error("The reference mask GeoTIFF must contain exactly one band.")
        st.stop()
    same_grid = (
        reference_data.shape[1:] == data.shape[1:]
        and reference_profile["crs"] == raster_profile["crs"]
        and reference_profile["transform"] == raster_profile["transform"]
    )
    if not same_grid:
        st.error(
            "The reference mask must have the same CRS, transform, width, and "
            "height as the uploaded cyclone GeoTIFF."
        )
        st.stop()

st.caption(f"Testing input: **{scene_label}**")
show_reference = st.sidebar.checkbox(
    "Show independent reference and metrics",
    value=False,
    disabled=not has_reference,
    help="Enable this for comparison with the aligned Copernicus/HDX flood reference.",
)
aggregate_reference = st.sidebar.checkbox(
    "Aggregate metrics across all valid patches",
    value=False,
    disabled=not (has_reference and show_reference),
    help=(
        "Run inference over every non-overlapping 256x256 tile with valid SAR "
        "and reference pixels, then report mean (macro) and overall (micro) metrics."
    ),
)
st.sidebar.header("Select a region")
max_y = max(height - PATCH_SIZE, 0)
max_x = max(width - PATCH_SIZE, 0)
best_position, best_valid_fraction = find_best_patch(data, PATCH_SIZE)
default_y, default_x = best_position
y0 = st.sidebar.slider("Vertical position", 0, max_y, default_y, step=PATCH_SIZE)
x0 = st.sidebar.slider("Horizontal position", 0, max_x, default_x, step=PATCH_SIZE)
threshold = st.sidebar.slider("Flood probability threshold", 0.0, 1.0, float(threshold_default), 0.05)
st.sidebar.caption(
    f"Best available patch has {best_valid_fraction * 100:.1f}% valid SAR pixels."
)

y1, x1 = y0 + PATCH_SIZE, x0 + PATCH_SIZE
patch = data[:, y0:y1, x0:x1]  # (6, 256, 256)

# The first four bands are always the model inputs. A sixth band is treated as
# the optional bundled training label; uploaded reference masks use the uploader.
band_name_to_index = {"pre_vv": 0, "pre_vh": 1, "post_vv": 2, "post_vh": 3}
input_indices = [band_name_to_index[b] for b in input_bands]
input_patch = patch[input_indices]
baseline_mask = patch[5] if patch.shape[0] > 5 else None
reference_patch = reference_data[0, y0:y1, x0:x1] if has_reference else None

valid_pixels = np.isfinite(input_patch).all(axis=0)
if not valid_pixels.any():
    st.warning(
        "This region contains no valid SAR pixels. Use the suggested best patch "
        f"near row {default_y}, column {default_x}, or choose another valid area."
    )
else:
    st.info(f"Valid SAR pixels in selected patch: {valid_pixels.mean() * 100:.1f}%")
    filled_input = np.where(np.isfinite(input_patch), input_patch, np.asarray(mean)[:, None, None])
    normed = normalise(filled_input, mean, std)
    tensor = torch.from_numpy(normed.astype(np.float32)).unsqueeze(0).to(device)  # (1, 4, 256, 256)

    with torch.no_grad():
        logits = model(tensor)
        prob = torch.sigmoid(logits).squeeze().cpu().numpy()  # (256, 256)
    pred_mask = ((prob > threshold) & valid_pixels).astype(np.uint8)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.image(to_display(patch[0]), caption="Pre-event VV", use_container_width=True)
        pre_valid = patch[0][np.isfinite(patch[0])]
        if pre_valid.size:
            st.caption(f"Finite-pixel mean: {float(pre_valid.mean()):.2f} dB")
    with col2:
        st.image(to_display(patch[2]), caption="Post-event VV", use_container_width=True)
        post_valid = patch[2][np.isfinite(patch[2])]
        if post_valid.size:
            st.caption(f"Finite-pixel mean: {float(post_valid.mean()):.2f} dB")
    with col3:
        if baseline_mask is not None:
            baseline_display = (np.nan_to_num(baseline_mask, nan=0.0) > 0.5).astype(np.uint8)
            st.image(
                baseline_display * 255,
                caption="Training label (SAR threshold)",
                use_container_width=True,
            )
        elif show_reference and reference_patch is not None:
            st.image(
                (reference_patch > 0.5).astype(np.uint8) * 255,
                caption="Independent reference mask",
                use_container_width=True,
            )
        else:
            st.info("Upload and enable an independent reference mask to compare.")
    with col4:
        st.image(pred_mask * 255, caption="Model prediction", use_container_width=True)

    flood_pct = 100 * pred_mask.mean()
    st.metric("Predicted flooded area in this patch", f"{flood_pct:.1f}%")

    st.subheader("Model prediction statistics")
    if show_reference and has_reference:
        st.caption("Metrics below compare the prediction with the independent reference mask.")
    else:
        st.caption("These are prediction statistics; independent accuracy metrics are unavailable.")

    if show_reference and reference_patch is not None:
        observed = reference_patch > 0.5
        evaluation_pixels = valid_pixels
        predicted = pred_mask.astype(bool)
        true_positive = int(np.count_nonzero(predicted & observed & evaluation_pixels))
        false_positive = int(np.count_nonzero(predicted & ~observed & evaluation_pixels))
        false_negative = int(np.count_nonzero(~predicted & observed & evaluation_pixels))
        true_negative = int(np.count_nonzero(~predicted & ~observed & evaluation_pixels))
        union = true_positive + false_positive + false_negative
        dice_denominator = 2 * true_positive + false_positive + false_negative
        metrics = {
            "IoU": true_positive / union if union else 1.0,
            "Dice / F1": 2 * true_positive / dice_denominator if dice_denominator else 1.0,
            "Precision": (
                true_positive / (true_positive + false_positive)
                if true_positive + false_positive
                else 0.0
            ),
            "Recall": (
                true_positive / (true_positive + false_negative)
                if true_positive + false_negative
                else 0.0
            ),
        }
        st.markdown("**Independent reference evaluation**")
        metric_columns = st.columns(4)
        for column, (label, value) in zip(metric_columns, metrics.items()):
            column.metric(label, f"{value:.3f}")
        st.dataframe(
            {
                "": ["Reference flooded", "Reference not flooded"],
                "Predicted flooded": [true_positive, false_positive],
                "Predicted not flooded": [false_negative, true_negative],
            },
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            f"Metrics use {int(evaluation_pixels.sum()):,} valid SAR pixels in this patch."
        )
        if aggregate_reference:
            with st.spinner("Evaluating all valid 256x256 patches..."):
                aggregate = aggregate_patch_metrics(
                    model,
                    data[input_indices].astype(np.float32),
                    reference_data[0].astype(np.float32),
                    mean,
                    std,
                    threshold,
                    device,
                    PATCH_SIZE,
                )
            macro = aggregate["macro_mean"]
            micro = aggregate["micro_overall"]
            st.markdown("**Aggregated independent-reference evaluation**")
            st.caption(
                f"Mean metrics across {aggregate['patch_count']:,} valid patches. "
                "Macro values give every patch equal weight; overall values pool all pixels."
            )
            st.dataframe(
                {
                    "Metric": ["IoU", "Dice / F1", "Precision", "Recall"],
                    "Mean across patches": [
                        macro["iou"],
                        macro["dice_f1"],
                        macro["precision"],
                        macro["recall"],
                    ],
                    "Overall across pixels": [
                        micro["iou"],
                        micro["dice_f1"],
                        micro["precision"],
                        micro["recall"],
                    ],
                },
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                f"Aggregated confusion matrix: TP {micro['true_positive']:,}, "
                f"FP {micro['false_positive']:,}, FN {micro['false_negative']:,}, "
                f"TN {micro['true_negative']:,}."
            )

    stats_col1, stats_col2 = st.columns(2)
    with stats_col1:
        st.markdown("**Predicted area by class**")
        st.bar_chart(
            {
                "Class": ["Not flooded", "Flooded"],
                "Pixels (%)": [100 - flood_pct, flood_pct],
            },
            x="Class",
            y="Pixels (%)",
        )

    with stats_col2:
        st.markdown("**Pixel flood-probability distribution**")
        bin_edges = np.linspace(0.0, 1.0, 11)
        bin_counts, _ = np.histogram(prob, bins=bin_edges)
        bin_labels = [
            f"{bin_edges[i]:.1f}-{bin_edges[i + 1]:.1f}" for i in range(len(bin_counts))
        ]
        st.bar_chart(
            {"Probability range": bin_labels, "Pixels": bin_counts},
            x="Probability range",
            y="Pixels",
        )
        st.caption("Probabilities near 0.5 indicate pixels where the model is less certain.")

    vv_stats = []
    for name, band in [("Pre-event VV", patch[0]), ("Post-event VV", patch[2])]:
        finite_band = band[np.isfinite(band)]
        if finite_band.size == 0:
            continue
        vv_stats.append(
            {
                "Image": name,
                "Mean (dB)": float(np.mean(finite_band)),
                "Minimum (dB)": float(np.min(finite_band)),
                "Maximum (dB)": float(np.max(finite_band)),
                "Std. deviation (dB)": float(np.std(finite_band)),
            }
        )
    vv_difference = patch[2] - patch[0]
    finite_difference = vv_difference[np.isfinite(vv_difference)]
    if finite_difference.size:
        vv_stats.append(
            {
                "Image": "Post - pre VV",
                "Mean (dB)": float(np.mean(finite_difference)),
                "Minimum (dB)": float(np.min(finite_difference)),
                "Maximum (dB)": float(np.max(finite_difference)),
                "Std. deviation (dB)": float(np.std(finite_difference)),
            }
        )
    st.markdown("**VV backscatter statistics**")
    st.dataframe(vv_stats, hide_index=True, use_container_width=True)

    st.caption(
        "Note: the training label is a -3.5 dB SAR-threshold heuristic, not independently "
        "verified ground truth. The model can largely reproduce this rule from its own inputs, "
        "so the IoU shown during training reflects consistency with that rule rather than "
        "proven real-world flood accuracy -- see docs/risk-analysis.md."
    )
