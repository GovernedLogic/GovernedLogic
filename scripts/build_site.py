#!/usr/bin/env python3
"""Build the reviewed public website artifact from an explicit allowlist."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]

# This list is the deployment boundary. Repository files not listed here remain
# available to Git history and review, but are not copied into the website.
PUBLIC_FILES = (
    "index.html",
    "challenge/index.html",
    "challenge/index.json",
    "concepts/ultimate-grounding/index.html",
    "company/index.html",
    "research/index.html",
    "library/index.html",
    "faq/index.html",
    "faq/index.json",
    "robots.txt",
    "sitemap.xml",
    "assets/opening.css",
    "assets/site-navigation.css",
    "assets/material-environment.js",
    "assets/earth-renderer.js",
    "assets/opening.js",
    "assets/materials/Cinzel-OFL.txt",
    "assets/materials/SOURCES.txt",
    "assets/materials/cinzel.ttf",
    "assets/materials/earth-clouds.jpg",
    "assets/materials/earth-day.jpg",
    "assets/materials/earth-night.jpg",
)


def validate_sources() -> None:
    unsafe = [
        relative
        for relative in PUBLIC_FILES
        if Path(relative).is_absolute() or ".." in Path(relative).parts
    ]
    if unsafe:
        raise SystemExit("Unsafe public file entries: " + ", ".join(unsafe))
    invalid = [
        relative
        for relative in PUBLIC_FILES
        if (ROOT / relative).is_symlink() or not (ROOT / relative).is_file()
    ]
    if invalid:
        raise SystemExit("Missing or non-regular public source files: " + ", ".join(invalid))


def safe_destination(value: str) -> Path:
    destination = Path(value).resolve()
    forbidden = {ROOT, ROOT.parent, Path(destination.anchor)}
    if destination in forbidden or destination.is_relative_to(ROOT):
        raise SystemExit(f"Refusing unsafe output directory: {destination}")
    if destination.exists() or destination.is_symlink():
        raise SystemExit(f"Output directory must not already exist: {destination}")
    return destination


def output_files(destination: Path) -> set[str]:
    return {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }


def build(destination: Path) -> None:
    validate_sources()
    destination.mkdir(parents=True)
    for relative in PUBLIC_FILES:
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    actual = output_files(destination)
    expected = set(PUBLIC_FILES)
    if actual != expected:
        raise SystemExit(
            f"Artifact boundary differs; extra={sorted(actual - expected)}, "
            f"missing={sorted(expected - actual)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Directory for the public site artifact")
    args = parser.parse_args()
    destination = safe_destination(args.output)
    build(destination)
    print(f"Built {len(PUBLIC_FILES)} reviewed public files in {destination}")


if __name__ == "__main__":
    main()
