"""Render and optimize all README and Wiki GIFs with Manim.

The script keeps Manim's intermediate media under docs/animations/media, then
writes compact, stable GIF filenames to docs/assets.
"""

from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageSequence


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = HERE / "lexical_analyzer.py"
MEDIA = HERE / "media"
ASSETS = REPO / "docs" / "assets"

SCENES = {
    "ThompsonConstruction": "thompson-construction.gif",
    "SubsetConstruction": "subset-construction.gif",
    "MaximalMunch": "maximal-munch.gif",
}

OUTPUT_WIDTH = 540
FRAME_STRIDE = 3
PALETTE_COLORS = [
    "0c0a09",
    "1c1917",
    "292524",
    "44403c",
    "57534e",
    "78716c",
    "a8a29e",
    "d6d3d1",
    "f5f5f4",
    "ffffff",
    "78350f",
    "92400e",
    "b45309",
    "d97706",
    "f59e0b",
    "fbbf24",
    "064e3b",
    "047857",
    "10b981",
    "34d399",
    "6ee7b7",
    "86efac",
    "1e3a8a",
    "1d4ed8",
    "3b82f6",
    "60a5fa",
    "93c5fd",
    "4c1d95",
    "7c3aed",
    "8b5cf6",
    "a78bfa",
    "c4b5fd",
    "be123c",
    "fb7185",
]


def project_palette() -> Image.Image:
    """Create a fixed palette that preserves the documentation theme."""
    palette_bytes = []
    for color in PALETTE_COLORS:
        palette_bytes.extend(bytes.fromhex(color))
    palette_bytes.extend([0] * (768 - len(palette_bytes)))

    palette = Image.new("P", (1, 1))
    palette.putpalette(palette_bytes)
    return palette


def optimize_gif(source: Path, destination: Path) -> None:
    """Resize and quantize a Manim GIF for practical README loading."""
    with Image.open(source) as image:
        duration = image.info.get("duration", 70) * FRAME_STRIDE
        output_height = round(image.height * OUTPUT_WIDTH / image.width)
        output_size = (OUTPUT_WIDTH, output_height)
        palette = project_palette()
        frames = []

        for index, frame in enumerate(ImageSequence.Iterator(image)):
            if index % FRAME_STRIDE:
                continue
            resized = frame.convert("RGB").resize(
                output_size,
                Image.Resampling.LANCZOS,
            )
            frames.append(
                resized.quantize(palette=palette, dither=Image.Dither.NONE)
            )

    if not frames:
        raise ValueError(f"No frames found in {source}")

    frames[0].save(
        destination,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=False,
        disposal=1,
    )


def render(scene: str, output_name: str) -> None:
    command = [
        sys.executable,
        "-m",
        "manim",
        "-ql",
        "--format=gif",
        "--fps=15",
        "--disable_caching",
        f"--media_dir={MEDIA}",
        str(SOURCE),
        scene,
    ]
    print(f"Rendering {scene}...")
    subprocess.run(command, cwd=HERE, check=True)

    candidates = sorted(
        MEDIA.rglob(f"{scene}*.gif"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"Manim did not produce {scene}.gif")

    ASSETS.mkdir(parents=True, exist_ok=True)
    destination = ASSETS / output_name
    optimize_gif(candidates[0], destination)
    size_kib = destination.stat().st_size / 1024
    print(f"Wrote {destination.relative_to(REPO)} ({size_kib:.0f} KiB)")


def main() -> None:
    for scene, output_name in SCENES.items():
        render(scene, output_name)


if __name__ == "__main__":
    main()
