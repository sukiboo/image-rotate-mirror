# Implementation Plan — Image Rotate & Mirror

## Goal
Web app: upload an image, position a draggable selection rectangle over a rotatable view, and produce two mirrored outputs (left half mirrored about its right edge, right half mirrored about its left edge). Deployable to Hugging Face Spaces.

## Stack
- **Streamlit** — UI framework (HF Spaces `sdk: streamlit`).
- **streamlit-cropper** — draggable/resizable selection rectangle; returns crop box and cropped region.
- **Pillow** — rotation, cropping, mirroring, encoding.
- (Optional) **numpy** — only if we need it for the inscribed-rectangle math.

## File layout
```
app.py             # Streamlit entry point — UI + event wiring only
mirror.py          # Pure image ops: rotate, mirror_pair, inscribed_bbox
constants.py       # Defaults: rotation range, preview size, max upload, etc.
mirror_split.py    # Existing CLI — refactor to import from mirror.py
requirements.txt   # streamlit, streamlit-cropper, pillow
README.md          # HF Spaces frontmatter + usage
.gitignore         # __pycache__, .env, *.pyc
images/            # Example inputs/outputs (already exists)
```

## UI layout
```
┌────────────────────────────────────────────┐
│ [ file uploader ]                          │
├──────────────────────────────┬─────────────┤
│                              │ rotation ▭  │
│   image with cropper         │             │
│   (draggable square)         │ size     ▭  │
│                              │             │
├──────────────┬───────────────┴─────────────┤
│ preview <A|A>│ preview <B|B>               │
├──────────────┴─────────────────────────────┤
│         [ download (saves both) ]          │
└────────────────────────────────────────────┘
```

- **Selection is square-locked** (cropper `aspect_ratio=(1, 1)`).
- **Size slider** on the right drives the cropper's box dimension (single value, since width = height when locked square). Position is set by dragging.
- **Rotation slider** on the right.
- **Single download button** that emits both PNGs. Implementation: `st.components.v1.html` rendering a `<button>` whose `onclick` triggers two `<a download>` clicks (data URIs from the encoded PNGs). Browsers will show a one-time "Allow multiple downloads?" prompt — acceptable.

## Data flow
1. **Upload** → `PIL.Image` in `st.session_state["src"]`.
2. **Rotate** by `θ` → `working` image (see "Rotation handling" below).
3. **Cropper** runs on `working`, returns `(x, y, w, h)` and the cropped region.
4. **Split + mirror** the cropped region → `left_out`, `right_out`.
5. **Render** both previews.
6. **Download** — single button (custom HTML/JS) that triggers two browser downloads: `<name>_left.png`, `<name>_right.png`.

Each Streamlit rerun (any slider tick, any cropper drag) re-runs steps 2–5. For typical image sizes this should be fast; if it stutters on large uploads we'll downscale for display while keeping full-res for the download path.

## Pure functions (`mirror.py`)
```python
def rotate(img: Image.Image, degrees: float) -> Image.Image: ...
def mirror_pair(region: Image.Image) -> tuple[Image.Image, Image.Image]: ...
def inscribed_bbox(width: int, height: int, degrees: float) -> tuple[int, int, int, int]: ...
```
- `mirror_pair` matches the convention already in `mirror_split.py`: left output is `left | mirror(left)`, right output is `mirror(right) | right`. (Diagram notation `<A | A>` describes the same thing — `<A` is the original left half, `A>` is its flip.)
- `inscribed_bbox` returns the largest axis-aligned rectangle that fits inside the rotated image, so the cropper never sees transparent corners.

`mirror_split.py` becomes a thin CLI wrapper over these — no logic duplication.

## Rotation handling
**Decision: crop to inscribed rectangle.** Rotate with `expand=True`, then crop to the largest axis-aligned rectangle that fits inside the rotated image. The cropper sees only real pixels, so the selection can never include transparent corners. Trade-off accepted: some image content is lost at non-90° angles.

## Phased implementation
1. **Scaffold** — `requirements.txt`, empty modules, `.gitignore`.
2. **`mirror.py`** — `rotate`, `mirror_pair`, `inscribed_bbox`. Refactor `mirror_split.py` to use them. Verify outputs byte-match existing `images/image_left.png` / `images/image_right.png`.
3. **Minimal app** — upload → cropper → previews. No rotation, no download yet. Confirm the loop feels right.
4. **Rotation** — slider + inscribed-rectangle clamping. Riskiest step; do it on its own.
5. **Download** — single button rendered via `st.components.v1.html`; JS click handler triggers two `<a download>` data-URI links. Verify behavior on Chrome + Firefox (the "allow multiple downloads" prompt is expected).
6. **Polish** — layout proportions, sensible default selection, max upload size, empty states.
7. **HF Spaces** — `README.md` frontmatter (`sdk: streamlit`, `sdk_version`, `app_file: app.py`), pin versions in `requirements.txt`, push.

## Open questions
- **Cropper interaction with size slider** — when the slider changes, the cropper's box should resize but keep its current center. streamlit-cropper's `default_coords` controls initial state; need to confirm it can be re-driven cleanly via session_state on each rerun without "jumping" the user's drag. Worst case: accept that a slider change re-centers the box. Verify in Phase 3.
- **Max upload size** — HF Spaces has memory limits. Soft-cap at e.g. 4096px on the longest side, downscale on upload? **Default: cap at 4096px, document it.**
- **Output naming** — `<original_name>_left.png` / `_right.png`? **Default: yes.**

## Out of scope (for v1)
- Multiple selections.
- Non-vertical splits.
- Batch processing.
- Auth, rate limiting, or persistence.
- Mobile layout tuning.
