# Watch Later

A static web app for browsing and editing a YouTube watch-later list stored as a **local JSON file**. The UI reads and writes that file with the browser’s [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API), so your list stays on your machine (or in a folder you sync yourself).

## Data file: `watch_later.json`

**This repository does not include a `watch_later.json`.** That file is your private list; you need to create it (or export/import through the app).

A simple way to work offline-first is to keep `watch_later.json` in a folder synced with **Google Drive** (or similar), open the app from Netlify or localhost, and use **Menu → Open JSON file** to pick that file. The browser can remember permission to the file across visits; after a full reload you may need to allow access again.

### Minimal format

The file is a JSON **array** of video objects. Typical fields:

| Field       | Type    | Notes |
|------------|---------|--------|
| `id`       | string  | YouTube video id |
| `title`    | string  | |
| `channel`  | string  | |
| `url`      | string  | Usually `https://www.youtube.com/watch?v=…` |
| `category` | string  | User-defined label |
| `duration` | number or `null` | Length in **seconds**; often filled later via `fetch_durations.py` |
| `watched`  | boolean | |
| `removed`  | boolean | Soft-remove from the active list |

Example starter file:

```json
[]
```

Or one entry:

```json
[
  {
    "id": "dQw4w9WgXcQ",
    "title": "Example",
    "channel": "Example Channel",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "category": "Uncategorized",
    "duration": null,
    "watched": false,
    "removed": false
  }
]
```

Use **Menu → Import / Merge** in the app to bring in more data without hand-editing.

## Requirements

- **Chrome or another Chromium-based browser** with File System Access support.
- **HTTPS or `http://localhost`** — the file picker does not work from a `file://` URL. [Netlify](https://www.netlify.com/) (and similar hosts) provide HTTPS by default.

## Host on Netlify

Point the site at this repo (or drag-and-drop the folder). Netlify serves `index.html` as the site root. You still open **your own** `watch_later.json` from disk (or from a synced folder) after the page loads; nothing in the deploy stores your list on the server.

## Local development

You need a local URL (not `file://`). Any static file server works:

- **VS Code / Cursor:** use a static-server extension (for example [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer)) and open the served page from the status bar or command palette. You do not need Python for this.
- **Terminal:** for example `python3 -m http.server 8080` from the project folder, then open `http://localhost:8080`.

## Filling in video durations

New entries often have `"duration": null`. To fill lengths using [yt-dlp](https://github.com/yt-dlp/yt-dlp):

```bash
pip install yt-dlp
python3 fetch_durations.py
```

### Where the script looks for `watch_later.json`

If your JSON lives in a synced folder (for example Google Drive) instead of next to the script, add a **`.env`** file next to `fetch_durations.py` (that file is gitignored) with:

```bash
WATCH_LATER_JSON_PATH="/Users/you/Library/CloudStorage/GoogleDrive-you@email.com/My Drive/watch_later/watch_later.json"
```

You can set the same variable in your shell instead of `.env`. Omit it to use `watch_later.json` in the same directory as `fetch_durations.py`.

**`--file` on the command line overrides** `WATCH_LATER_JSON_PATH` for that run only.

Optional arguments:

```bash
python3 fetch_durations.py --file /path/to/watch_later.json
python3 fetch_durations.py --limit 50
```

The app can copy `python3 fetch_durations.py` from the menu after you load a file; that matches `WATCH_LATER_JSON_PATH` from `.env`/environment or a JSON file next to the script.

## Repo layout

| Path | Purpose |
|------|--------|
| `index.html` | App |
| `favicon.svg` | Site icon |
| `fetch_durations.py` | Optional CLI to backfill `duration` |
| `archive/` | Legacy `watch_later.html`, design notes, reference exports |

## Privacy

The hosted app is static HTML/CSS/JS. Your list is only ever read from and written to the JSON file you choose on your device (or in a synced folder you control).
