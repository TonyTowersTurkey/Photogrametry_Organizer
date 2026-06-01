# organize_photos.py

Small script to organize photos by timestamp into a year/month/day folder hierarchy.

Features
- Organizes JPEG/RAW files by EXIF DateTimeOriginal when available, otherwise falls back to filesystem timestamps.
- Renames files to `YYYYMMDD_HHMMSS.ext` and avoids collisions by appending `_01`, `_02`, etc.
- `--dry-run` to preview actions and `--verbose`/`-v` for more output.

Quick usage

Run with positional paths:

```bash
python organize_photos.py /path/to/source /path/to/dest
```

Run with named options:

```bash
python organize_photos.py --source ~/DCIM --dest ~/Photos/Drone --dry-run -v
```

Flags
- `--source, -s`: Source directory containing photos (optional; can be positional)
- `--dest, -d`: Destination directory for organized photos (optional; can be positional)
- `--dry-run, -n`: Show actions without moving files
- `--verbose, -v`: Increase verbosity (use `-v` or `-vv`)

Install / make available globally

1) Simple symlink (fast, personal):

```bash
chmod +x /path/to/organize_photos.py
mkdir -p ~/bin
ln -s /path/to/organize_photos.py ~/bin/organize_photos
# ensure ~/bin is in your PATH
```

2) Virtualenv (isolated dependencies):

```bash
python -m venv .venv
source .venv/bin/activate
pip install Pillow
python organize_photos.py -s ~/DCIM -d ~/Photos/Drone
```

3) Packaging (for distribution):
- Add a `pyproject.toml` with a `console_scripts` entry and `Pillow` in `requires` so `pip install .` creates an executable.

Cron / scheduling example

Run nightly (edit crontab with `crontab -e`):

```cron
0 2 * * * /usr/bin/python3 /path/to/organize_photos.py -s /media/drive/DCIM -d /media/drive/Photos/Organized --dry-run >> /var/log/organize_photos.log 2>&1
```

Notes
- The script prefers absolute paths; `~` is expanded. Use `--dry-run` first to verify actions.
- If you need more detailed logging, I can switch the script to use Python's `logging` module and map `-v` to log levels.
