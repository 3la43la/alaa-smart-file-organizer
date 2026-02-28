#!/usr/bin/env python3
"""
organize_files.py
نقل/نسخ الملفات إلى مجلدات بحسب امتداداتها.

Usage examples:
  python organize_files.py -s /path/to/source --recursive
  python organize_files.py -s ~/Downloads -d ~/Desktop/Organized --action copy --dry-run
  python organize_files.py -s . --map custom_map.json

Custom map JSON format:
{
  "Videos": ["mp4", "mkv", "mov"],
  "Images": ["jpg", "png", "gif"],
  "MyDocs": ["pdf", "docx"]
}
"""
from pathlib import Path
import shutil
import argparse
import json
import logging
from collections import defaultdict

# الخريطة الافتراضية (قابلة للتعديل)
DEFAULT_MAP = {
    "Videos": ["mp4", "mkv", "mov", "avi", "flv", "wmv", "webm", "m4v"],
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg", "webp"],
    "Documents": ["pdf", "doc", "docx", "txt", "odt", "rtf", "xls", "xlsx", "ppt", "pptx"],
    "Audio": ["mp3", "wav", "aac", "flac", "ogg", "m4a"],
    "Archives": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"],
    "Code": ["py", "js", "java", "c", "cpp", "cs", "rb", "go", "rs", "php", "html", "css", "ts"],
    "Fonts": ["ttf", "otf", "woff", "woff2"],
    "Spreadsheets": ["csv"],
    "Presentations": ["key"]
}
OTHER_FOLDER_NAME = "Others"

def build_ext_map(map_by_category):
    ext_to_cat = {}
    for cat, exts in map_by_category.items():
        for e in exts:
            ext_to_cat[e.lower().lstrip(".")] = cat
    return ext_to_cat

def load_custom_map(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Custom map must be a JSON object mapping folder->list_of_exts")
        # Normalize: ensure each value is list
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = [v]
            elif not isinstance(v, list):
                raise ValueError("Each mapping value must be list of extensions.")
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to load custom map '{path}': {e}")

def make_unique_path(dest: Path):
    if not dest.exists():
        return dest
    stem = dest.stem
    suf = dest.suffix
    parent = dest.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suf}"
        if not candidate.exists():
            return candidate
        i += 1

def organize(source: Path, dest_root: Path, ext_map: dict, recursive: bool,
             action: str, dry_run: bool, include_hidden: bool):
    files_moved = 0
    files_skipped = 0
    per_category = defaultdict(int)

    if recursive:
        iterator = source.rglob("*")
    else:
        iterator = source.iterdir()

    for p in iterator:
        try:
            if p.is_dir():
                continue
            # optionally skip hidden files
            if not include_hidden and p.name.startswith("."):
                files_skipped += 1
                continue
            ext = p.suffix.lower().lstrip(".")
            cat = ext_map.get(ext, OTHER_FOLDER_NAME)
            target_dir = dest_root / cat
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / p.name
            target = make_unique_path(target)
            if dry_run:
                logging.info("[DRY-RUN] %s -> %s", str(p), str(target))
            else:
                if action == "move":
                    shutil.move(str(p), str(target))
                    logging.info("Moved: %s -> %s", str(p), str(target))
                else:
                    # copy (preserve metadata)
                    shutil.copy2(str(p), str(target))
                    logging.info("Copied: %s -> %s", str(p), str(target))
            files_moved += 1
            per_category[cat] += 1
        except Exception as e:
            logging.warning("Failed to process %s: %s", p, e)
            files_skipped += 1

    return files_moved, files_skipped, per_category

def main():
    parser = argparse.ArgumentParser(description="Organize files into folders by extension.")
    parser.add_argument("-s", "--source", default=".", help="Source folder (default: current dir)")
    parser.add_argument("-d", "--dest", default=None, help="Destination root folder (default: same as source)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Organize recursively")
    parser.add_argument("-a", "--action", choices=["move", "copy"], default="move", help="Move files (default) or copy them")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be done without changing files")
    parser.add_argument("--map", "-m", help="JSON file with custom mapping (folder -> list of extensions)")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files (those starting with .)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s: %(message)s")

    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        parser.error(f"Source folder does not exist or is not a directory: {source}")

    dest_root = Path(args.dest).expanduser().resolve() if args.dest else source

    # Build mapping
    map_by_category = dict(DEFAULT_MAP)  # copy
    if args.map:
        custom_map_path = Path(args.map).expanduser()
        custom_map = load_custom_map(custom_map_path)
        # Merge: custom categories override/add
        map_by_category.update(custom_map)
    ext_map = build_ext_map(map_by_category)

    logging.info("Source: %s", source)
    logging.info("Destination root: %s", dest_root)
    logging.info("Action: %s", args.action)
    logging.info("Recursive: %s", args.recursive)
    logging.info("Dry-run: %s", args.dry_run)
    logging.info("Custom categories: %s", ", ".join(map_by_category.keys()))

    files_moved, files_skipped, per_category = organize(
        source, dest_root, ext_map, args.recursive, args.action, args.dry_run, args.include_hidden
    )

    logging.info("Done. Processed: %d files. Skipped/failed: %d", files_moved, files_skipped)
    logging.info("Per-category counts:")
    for cat, cnt in per_category.items():
        logging.info("  %s: %d", cat, cnt)

if __name__ == "__main__":
    main()