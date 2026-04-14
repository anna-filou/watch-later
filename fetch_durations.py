#!/usr/bin/env python3
"""
fetch_durations.py
Reads watch_later.json, fetches missing durations via yt-dlp,
and writes the results back to the same file after each batch
(so you keep progress if the run is interrupted).

Usage:
    python3 fetch_durations.py
    python3 fetch_durations.py --file /path/to/watch_later.json   # overrides .env / env
    python3 fetch_durations.py --limit 50   # only fetch first N missing

Default JSON path: WATCH_LATER_JSON_PATH in the environment, or in a .env file next to
this script (gitignored), else watch_later.json in this directory.
"""

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


def load_local_env() -> None:
    """Load KEY=value lines from .env next to this script (does not override existing os.environ)."""
    path = Path(__file__).resolve().parent / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val

def parse_args():
    p = argparse.ArgumentParser(description="Fetch missing YouTube durations via yt-dlp")
    p.add_argument(
        "--file",
        default=None,
        metavar="PATH",
        help="Path to watch_later.json (overrides WATCH_LATER_JSON_PATH from env / .env)",
    )
    p.add_argument("--limit", type=int, default=None, help="Max number of missing durations to fetch")
    return p.parse_args()


def resolved_json_path(cli_file: str | None) -> Path:
    if cli_file:
        return Path(cli_file).expanduser().resolve()
    env_path = (os.environ.get("WATCH_LATER_JSON_PATH") or "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path(__file__).resolve().parent / "watch_later.json"

def fetch_durations_batch(
    video_ids: list[str],
    *,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, int | None]:
    """Fetch durations for a list of video IDs using yt-dlp.

    Streams stdout line-by-line so *progress* can run after each video
    (current index 1-based, total = len(video_ids)).
    """
    urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
    result: dict[str, int | None] = {}
    n = len(video_ids)
    cmd = [
        "yt-dlp",
        "--no-download",
        "--print",
        "%(id)s %(duration)s",
        "--no-warnings",
        "--ignore-errors",
    ] + urls

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print("ERROR: yt-dlp not found. Install it with: pip install yt-dlp")
        sys.exit(1)

    if proc.stdout is None:
        return result

    seen = 0
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 2:
                vid_id, dur = parts
                try:
                    result[vid_id] = int(float(dur))
                except ValueError:
                    result[vid_id] = None
                seen += 1
                if progress is not None:
                    progress(seen, n)
    finally:
        try:
            proc.wait(timeout=300)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            print("\nWARNING: yt-dlp timed out for this batch. Partial lines were captured.")

    return result


def write_videos(path: Path, videos: list) -> None:
    """Write the full video list to JSON (same formatting as the rest of the app)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def main():
    load_local_env()
    args = parse_args()
    data_path = resolved_json_path(args.file)

    if not data_path.exists():
        print(f"ERROR: File not found: {data_path}")
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        videos = json.load(f)

    missing = [v for v in videos if not v.get("removed") and v.get("duration") is None]
    if args.limit:
        missing = missing[:args.limit]

    total = len(missing)
    if total == 0:
        print("All videos already have durations. Nothing to do.")
        return

    print(f"Fetching durations for {total} videos (this may take a few minutes)...")
    print("(JSON is saved after each batch.)\n")

    lookup = {v["id"]: v for v in videos}
    chunk_size = 50
    num_batches = -(-total // chunk_size)
    updated_total = 0

    for i in range(0, total, chunk_size):
        chunk = missing[i : i + chunk_size]
        ids = [v["id"] for v in chunk]
        batch_n = i // chunk_size + 1

        def on_progress(cur: int, tot: int) -> None:
            # \033[K clears to end of line so shorter strings don’t leave junk when using \r
            print(
                f"\r  Batch {batch_n}/{num_batches}  video {cur}/{tot}\033[K",
                end="",
                flush=True,
            )

        results = fetch_durations_batch(ids, progress=on_progress)
        print()  # leave the progress line visible before the summary

        got = sum(1 for v in results.values() if v is not None)

        batch_updated = 0
        for vid_id, duration in results.items():
            if vid_id in lookup and duration is not None:
                lookup[vid_id]["duration"] = duration
                batch_updated += 1

        updated_total += batch_updated
        write_videos(data_path, videos)
        print(f"     yt-dlp lines {got}/{len(ids)} with duration → +{batch_updated} saved → {data_path}")

    print(f"\nDone. Updated {updated_total}/{total} durations in {data_path}")
    failed = total - updated_total
    if failed:
        print(f"  {failed} videos could not be fetched (private/deleted/unavailable).")

if __name__ == "__main__":
    main()
