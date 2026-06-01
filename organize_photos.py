#!/usr/bin/env python3
import argparse
import os
import shutil
import datetime
from pathlib import Path


'''
Organize photos by timestamp into destination folders.

This is a renamed, more generic version of the original importDronePics.py.
'''


# Default source/destination paths used when no arguments are provided
DEFAULT_SOURCE_DIR = os.path.expanduser("~/Desktop/DroneYess")
DEFAULT_DEST_DIR = os.path.expanduser("~/Desktop/DroneOrganized")


# File extensions to treat as photos
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".raw"}  # case-insensitive



def get_exif_datetime(path: Path):
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        return None

    try:
        with Image.open(path) as img:
            exif = img._getexif()
    except Exception:
        return None

    if not exif:
        return None

    date_str = None
    for tag_id, value in exif.items():
        tag = TAGS.get(tag_id, tag_id)
        if tag in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            date_str = value
            break

    if not date_str:
        return None

    try:
        return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def get_filesystem_datetime(path: Path) -> datetime.datetime:
    stat = path.stat()
    if hasattr(stat, "st_birthtime"):
        timestamp = stat.st_birthtime
    else:
        timestamp = stat.st_mtime
    return datetime.datetime.fromtimestamp(timestamp)


def get_photo_datetime(path: Path) -> datetime.datetime:
    ext = path.suffix.lower()
    dt = None
    if ext in {".jpg", ".jpeg"}:
        dt = get_exif_datetime(path)
    if dt is None:
        dt = get_filesystem_datetime(path)
    return dt


def ensure_unique_filename(dest_dir: Path, base_name: str, ext: str) -> Path:
    candidate = dest_dir / f"{base_name}{ext}"
    if not candidate.exists():
        return candidate
    counter = 1
    while True:
        candidate = dest_dir / f"{base_name}_{counter:02d}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize_photos(source: Path, dest: Path, dry_run: bool = False, verbose: int = 0):
    if not source.exists():
        print(f"Source directory does not exist: {source}")
        return

    if dry_run:
        if verbose:
            print(f"[dry-run] Would ensure destination exists: {dest}")
    else:
        dest.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Scanning source: {source}")

    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        for name in files:
            src_path = root_path / name
            ext = src_path.suffix.lower()
            if ext not in PHOTO_EXTENSIONS:
                if verbose > 1:
                    print(f"Skipping non-photo: {src_path}")
                continue
            dt = get_photo_datetime(src_path)
            year_str = dt.strftime("%Y")
            month_str = dt.strftime("%Y_%m")
            day_str = dt.strftime("%Y_%m_%d")
            day_dir = dest / year_str / month_str / day_str
            if dry_run:
                if verbose:
                    print(f"[dry-run] Would create directory: {day_dir}")
            else:
                day_dir.mkdir(parents=True, exist_ok=True)
            base_name = dt.strftime("%Y%m%d_%H%M%S")
            dest_path = ensure_unique_filename(day_dir, base_name, ext)
            if dry_run:
                print(f"[dry-run] {src_path} -> {dest_path}")
            else:
                if verbose:
                    print(f"Moving {src_path} -> {dest_path}")
                shutil.move(str(src_path), str(dest_path))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Organize photos by timestamp into destination folders.")
    parser.add_argument("pos_source", nargs="?", help="Positional source directory (optional)")
    parser.add_argument("pos_dest", nargs="?", help="Positional destination directory (optional)")
    parser.add_argument("--source", "-s", dest="source", help="Source directory containing photos")
    parser.add_argument("--dest", "-d", dest="dest", help="Destination directory for organized photos")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done without moving files")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity (use -v or -vv)")
    return parser.parse_args()


def ask_for_path(prompt: str, default: str) -> str:
    response = input(f"{prompt} [{default}]: ").strip()
    return response or default


if __name__ == "__main__":
    args = parse_arguments()
    source_path = args.source or args.pos_source or ask_for_path("Enter source path", DEFAULT_SOURCE_DIR)
    dest_path = args.dest or args.pos_dest or ask_for_path("Enter destination path", DEFAULT_DEST_DIR)
    src = Path(os.path.expanduser(source_path))
    dst = Path(os.path.expanduser(dest_path))
    organize_photos(src, dst, dry_run=args.dry_run, verbose=(args.verbose or 0))
