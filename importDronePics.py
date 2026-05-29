#!/usr/bin/env python3
import os
import shutil
import datetime
from pathlib import Path


'''
Scan ~/Desktop/DCIM (recursively).

Pick up .JPG/.JPEG/.RAW (case-insensitive).

Try to get the EXIF “DateTimeOriginal” when possible; if not, it falls back to the file’s modification time.

Rename each photo to a timestamp like YYYYMMDD_HHMMSS.ext.

Place it in ~/Desktop/drone/YYYY/MM/DD/.

Avoid empty day folders by only creating a folder when placing at least one file.

Handle collisions by appending _01, _02, etc. when needed.'''


# ---- CONFIGURE THESE ----
#SOURCE_DIR = os.path.expanduser("/Volumes/Untitled")
SOURCE_DIR = os.path.expanduser("~/Desktop/DroneYess")

DEST_DIR = os.path.expanduser("~/Desktop/DroneOrganized")
#DEST_DIR = os.path.expanduser("/Volumes/rootFolder/Photogrametry/Drone_Motel")


# File extensions to treat as photos
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".raw"}  # case-insensitive



def get_exif_datetime(path: Path):
    """
    Try to read the EXIF DateTimeOriginal/DateTime from a JPG using Pillow.
    Returns a datetime.datetime or None if not available.
    """
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

    # EXIF date format: "YYYY:MM:DD HH:MM:SS"
    try:
        return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def get_filesystem_datetime(path: Path) -> datetime.datetime:
    """
    Prefer filesystem creation time (birth time) if available (macOS),
    otherwise fall back to modification time.
    """
    stat = path.stat()

    # macOS and some BSDs expose st_birthtime
    if hasattr(stat, "st_birthtime"):
        timestamp = stat.st_birthtime
    else:
        # fallback for filesystems without birthtime
        timestamp = stat.st_mtime

    return datetime.datetime.fromtimestamp(timestamp)


def get_photo_datetime(path: Path) -> datetime.datetime:
    """
    Get the best guess for the photo timestamp:
    1. EXIF DateTimeOriginal (for JPEGs where possible)
    2. Filesystem creation time (birthtime) if available
    3. Otherwise, modification time
    """
    ext = path.suffix.lower()
    dt = None

    if ext in {".jpg", ".jpeg"}:
        dt = get_exif_datetime(path)

    if dt is None:
        dt = get_filesystem_datetime(path)

    return dt


def ensure_unique_filename(dest_dir: Path, base_name: str, ext: str) -> Path:
    """
    Ensure we don't overwrite files. If base_name.ext exists,
    try base_name_01.ext, base_name_02.ext, etc.
    """
    candidate = dest_dir / f"{base_name}{ext}"
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = dest_dir / f"{base_name}_{counter:02d}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize_photos(source: Path, dest: Path):
    if not source.exists():
        print(f"Source directory does not exist: {source}")
        return

    dest.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        for name in files:
            src_path = root_path / name
            ext = src_path.suffix.lower()

            if ext not in PHOTO_EXTENSIONS:
                continue  # skip non-photo files

            # Get timestamp
            dt = get_photo_datetime(src_path)

            year_str = dt.strftime("%Y")
            month_str = dt.strftime("%Y_%m")
            day_str = dt.strftime("%Y_%m_%d")

            # Build destination directory: ~/Desktop/drone/YYYY/YYYY_MM/YYYY_MM_DD
            day_dir = dest / year_str / month_str / day_str

            # Create only when we have at least one file to move
            day_dir.mkdir(parents=True, exist_ok=True)

            # Build base filename from timestamp: YYYYMMDD_HHMMSS
            base_name = dt.strftime("%Y%m%d_%H%M%S")
            dest_path = ensure_unique_filename(day_dir, base_name, ext)

            # Move and rename file
            print(f"Moving {src_path} -> {dest_path}")
            shutil.move(str(src_path), str(dest_path))


if __name__ == "__main__":
    src = Path(SOURCE_DIR)
    dst = Path(DEST_DIR)
    organize_photos(src, dst)
