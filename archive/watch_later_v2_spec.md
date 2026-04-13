## Watch Later App — Claude Code Build Spec

### Context
I have an existing YouTube Watch Later app (`watch_later.html`) that has all the features working. I need a new version (`watch_later_v2.html`) that separates the data from the UI. The data lives in `watch_later.json` and the app reads/writes it using the File System Access API.

---

### Files to create
- `watch_later_v2.html` — the new app
- `fetch_durations.py` — standalone script to fill in missing durations
- `watch_later.json` — already exists, don't overwrite it

---

### Tech constraints
- Single HTML file, no build step, no frameworks, no npm
- Vanilla JS only
- Fonts from Google Fonts: Syne (headings) + DM Sans (body)
- Works on `http://localhost` (VS Code Live Server) and `https://` (Netlify)
- File System Access API for reading/writing the JSON — Chrome/Edge only
- No data baked into the HTML

---

### Design
- Dark theme: `--bg: #0e0e10`, `--surface: #17171a`, `--surface2: #1f1f24`, `--border: #2a2a30`
- Accent: `--accent: #e8ff47` (yellow-green)
- Text: `--text: #f0f0f2`, `--muted: #8888a0`, `--muted2: #7878a0`
- All text must have lightness ≥ 50% for readability
- Responsive grid using `auto-fill minmax(220px, 1fr)`, collapses to ~160px on mobile
- Border radius: `--r: 10px`

---

### watch_later.json schema
Each video object:
```json
{
  "id": "youtube_video_id",
  "title": "Video title",
  "channel": "Channel name",
  "url": "https://www.youtube.com/watch?v=...",
  "category": "Design",
  "duration": null,
  "watched": false,
  "removed": false
}
```
`category` is an empty string `""` for uncategorized videos. `duration` is seconds as an integer or `null`.

---

### App flow

**Splash screen** (shown before a file is loaded):
- Shows the app name, a short explanation, and an "Open watch_later.json" button
- Uses `window.showOpenFilePicker()` to let the user pick the JSON file
- After picking, hides the splash and shows the main app
- On subsequent opens, Chrome may remember the file permission — handle gracefully

**Main app** (shown after file is loaded):
- Reads videos from JSON on load
- All changes (watched, removed, category, new videos) are written back to the JSON file immediately via `fileHandle.createWritable()`
- Never reloads the page — everything is in-memory + persisted to file

---

### Header layout
- Left: "Watch Later" title (Syne, 800 weight) + yellow badge with total non-removed video count
- Right: action buttons in a row — "Add video", "Import JSON", "Export" (dropdown), file icon to re-open file
- Below: controls row — search input, category dropdown, status dropdown, result count

---

### Category dropdown options (in order)
1. All categories (value: `""`)
2. Uncategorized (value: `"__uncategorized__"`)
3. All categories that exist in the loaded data, sorted alphabetically

When "Uncategorized" is selected, show only videos where `category === ""`

---

### Status dropdown
- Not watched (default, value: `"unwatched"`) — shows videos where `watched === false`
- Watched (value: `"watched"`) — shows videos where `watched === true`
- Everything (value: `"all"`) — shows all non-removed videos

---

### Active filter pill
Below the controls row, when a category is selected (not "All" or "Uncategorized"), show a dismissible pill: `Filtered by: [Category name] ×`

---

### Video card
- Thumbnail from `https://img.youtube.com/vi/{id}/mqdefault.jpg`, 16:9 aspect ratio
- On image error, show a placeholder with a ▶ symbol
- Hover: card lifts (`translateY(-3px)`), thumbnail scales slightly, play button overlay appears
- If `watched === true`: card is dimmed (opacity 0.5) + green "✓ Watched" overlay on thumbnail
- Duration: shown as a pill overlay on bottom-right of thumbnail (e.g. `4:32`, `1:03:20`). Hidden if `duration === null`
- Batch selected: accent-colored border + checkmark circle in top-right of thumbnail
- Card body: title (2-line clamp), then channel name + category tag
- Category tag: only shown when "All categories" is selected (redundant otherwise)
- Uncategorized videos: show a grey "Uncategorized" tag that opens the category picker when tapped
- Category tag colors: defined in a `CAT_COLORS` object (see below)

---

### CAT_COLORS object
```js
const CAT_COLORS = {
  "AI Design":         ["#d6eaff","#0e2a4a"],
  "AI Coding":         ["#c7e0ff","#0d2540"],
  "Design":            ["#ddd6ff","#1e1040"],
  "Productivity":      ["#d6fff0","#0a3020"],
  "PKM":               ["#b8f5d8","#083020"],
  "Mental Health":     ["#fff3c0","#3a2800"],
  "LGBT":              ["#ffd6f5","#3a0830"],
  "Self-Improvement":  ["#ffe5c0","#3a1800"],
  "Tech Reviews":      ["#2a2a3e","#c8c8e0"],
  "Politics & Society":["#ffd6d6","#3a0808"],
  "Fitness":           ["#d6ffe8","#0a2818"],
  "Language Learning": ["#ead6ff","#1e0838"],
  "Arcane":            ["#c0e8ff","#082030"],
  "Travel & Packing":  ["#fffbc0","#302800"],
  "Business":          ["#ffe8d6","#302008"],
  "Religion":          ["#2a2a2a","#d8d8d8"],
  "Philosophy":        ["#f0d6ff","#200838"],
  "Humor":             ["#fffbd6","#302600"],
  "Music":             ["#ffd6e8","#380820"],
  "Pop Culture":       ["#ffd6d8","#380810"],
  "Journalism":        ["#ffebd6","#382010"],
  "Short Films":       ["#d6e8ff","#0a1e38"],
  "Science & Health":  ["#d6ffec","#083020"],
  "Content Creation":  ["#fff4d6","#302800"],
  "Tech Culture":      ["#d6d6ff","#101038"],
  "Misc":              ["#2a2a2a","#c8c8c8"],
};
```
`ALL_CATS = Object.keys(CAT_COLORS).sort()` — used for the category picker modal.

---

### Load more
- Show 60 cards at a time
- "Load more" button at the bottom, only visible when there are more results

---

### Batch select mode

**Entry points:**
- Long press on a card (500ms) on mobile → enters batch mode + selects that card
- Right-click on a card on desktop → enters batch mode + selects that card
- On mobile, `contextmenu` events fired by long press must be ignored (check `e.pointerType === 'touch'` and `longPressed` flag)
- After long press fires, the synthetic `click` event that follows must be suppressed (use `longPressed` flag + `e.preventDefault() + e.stopPropagation()`)
- In batch mode, tapping/clicking a card toggles its selection — must NOT open the URL (`e.preventDefault()` on click, `e.preventDefault()` on mousedown too)

**Batch bar:**
- Sticky at `top: 0`, `z-index: 200`
- Shown only in batch mode
- Contains: selected count, "Select all" (toggles all visible cards), "Set category", "Toggle watched", "Remove", "× Cancel"
- "Select all" selects all currently visible/filtered cards, not all 890
- After any batch action, exit batch mode, save to file, re-render, show toast

**Escape key:** exits batch mode if active, otherwise closes any open modal

---

### Category picker modal
Used for both single-video and batch category assignment.

- Opens when: tapping "Uncategorized" tag on a card, or tapping "Set category" in batch bar
- Shows a grid of all 26 category pills, each styled with its CAT_COLORS bg/fg
- Currently assigned category is pre-selected (highlighted with accent border)
- Tap a pill to select it
- "Apply" button saves and closes
- For single video: updates that video's category
- For batch: updates all selected videos' categories, then exits batch mode
- After applying: save to file, rebuild category dropdown, re-render, show toast

---

### Add video modal

Steps:
1. User pastes a YouTube URL
2. Clicks "Fetch title & channel" — app calls `https://www.youtube.com/oembed?url=...&format=json`
3. If successful: shows a preview card with title and channel name, hides the fetch button, shows "Add video" button
4. Duration is always `null` on add — show a note "(run fetch_durations.py later)"
5. Category picker (same grid as category modal) is shown below the preview — default is no category selected (empty string)
6. Clicking "Add video": prepends video to `videos` array, saves to file, rebuilds category select, re-renders, closes modal, shows toast
7. If video ID already exists and is not removed: show toast "Already in your list"
8. If video ID already exists and is removed: restore it (set `removed: false`), show toast "Video restored"

---

### Import JSON modal
- "Import JSON" button in header opens a hidden `<input type="file" accept=".json">`
- After file is picked: parse the JSON, show a confirmation modal with summary (N videos, X watched, Y removed)
- On confirm: replace `videos` array, save to file, rebuild category select, re-render
- The imported JSON must be an array — validate and show error toast if not

---

### Export dropdown
Three options:
1. **Download JSON** — exports all non-removed videos as a JSON array with all fields, filename: `watch_later_YYYY-MM-DD.json`
2. **Download CSV** — exports all non-removed videos, columns: `id, title, channel, category, duration, watched, url`, filename: `watch_later_YYYY-MM-DD.csv`
3. **Copy fetch_durations cmd** — copies `python3 fetch_durations.py` to clipboard, shows toast "Command copied — paste in your terminal"

---

### Toast notifications
- Fixed position, bottom-center
- Auto-hides after 3 seconds
- Error toasts: red border
- Success: default border

---

### fetch_durations.py
Standalone Python script. Requirements: `yt-dlp` installed.

```
Usage:
  python3 fetch_durations.py
  python3 fetch_durations.py --file /path/to/watch_later.json
  python3 fetch_durations.py --limit 50
```

Logic:
1. Read `watch_later.json`
2. Find all videos where `duration === null` and `removed === false`
3. If `--limit` is set, take only the first N
4. Batch them in chunks of 50
5. For each chunk, call: `yt-dlp --no-download --print "%(id)s %(duration)s" --no-warnings --ignore-errors [urls...]`
6. Parse output: each line is `video_id duration_in_seconds`
7. Update `duration` field for matched videos
8. Write updated JSON back to file
9. Print progress and summary

---

### Things to be careful about

- The File System Access API requires `https://` or `http://localhost` — it won't work on `file://` URLs. Add a note in the splash screen.
- `window.showOpenFilePicker` returns an array — destructure: `[fileHandle] = await window.showOpenFilePicker(...)`
- Writing back to file: always use `fileHandle.createWritable()` then `writable.write(JSON.stringify(videos, null, 2))` then `writable.close()`
- The category dropdown should be rebuilt after any operation that might add new categories (add video, import, set category)
- When migrating from old format: ensure `duration`, `watched`, `removed`, `category` fields all exist on every video object after loading
- Long press on mobile fires `touchstart` → (500ms later) your handler → `touchend` → synthetic `click`. The click must be suppressed using a `longPressed` boolean flag that is reset after suppression.
- Right-click on desktop fires `contextmenu`. Guard it with `if (e.pointerType === 'touch' || longPressed) return` to avoid double-firing on mobile.
- In batch mode: `mousedown` should call `e.preventDefault()` to stop the browser treating the tap as a link press before click fires.
- Duration formatting: `seconds → "M:SS"` or `"H:MM:SS"`. Never show `null` — just omit the overlay.