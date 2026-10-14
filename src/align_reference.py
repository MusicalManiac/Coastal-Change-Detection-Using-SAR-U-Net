"""Align an Idai flood reference raster to a Sentinel-1 stack grid."""

from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--stack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with rasterio.open(args.stack) as stack:
        profile = stack.profile.copy()
        profile.update(count=1, dtype="uint8", nodata=0, compress="lzw")
        destination = np.zeros((stack.height, stack.width), dtype=np.uint8)
        destination_transform = stack.transform
        destination_crs = stack.crs

    with rasterio.open(args.reference) as reference:
        source = reference.read(1)
        source = np.where(source == reference.nodata, 0, source).astype(np.uint8)
        reproject(
            source=source,
            destination=destination,
            src_transform=reference.transform,
            src_crs=reference.crs,
            dst_transform=destination_transform,
            dst_crs=destination_crs,
            dst_nodata=0,
            resampling=Resampling.nearest,
        )

    destination = (destination > 0).astype(np.uint8)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(args.output, "w", **profile) as output:
        output.write(destination, 1)

    print(f"Wrote aligned reference: {args.output}")
    print(f"Flood pixels: {int(destination.sum())}")
    print(f"Total pixels: {destination.size}")


if __name__ == "__main__":
    main()
