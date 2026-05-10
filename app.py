import base64
import io
import json

import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper

from mirror import mirror_pair, rotate_full

ROTATION_MIN = -360
ROTATION_MAX = 360
ROTATION_STEP = 1
DEFAULT_ROTATION = 0
MIN_SELECTION = 32
DEFAULT_IMAGE = "images/cow.jpeg"
MAX_APP_SIZE = 1200
GAP_PX = 16
CROPPER_HEIGHT = MAX_APP_SIZE // 2
PREVIEW_HEIGHT = (CROPPER_HEIGHT - GAP_PX) // 2
CROPPER_STROKE = 2
CROPPER_BOX_COLOR = "#9ca3af"
CHECKER_DARK = "#c6c6c6"
CHECKER_LIGHT = "#d0d0d0"
CHECKER_CELL = 10
DIM_ALPHA = 96


def _png_b64(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


st.set_page_config(page_title="Image Rotate & Mirror", layout="wide")
st.markdown(
    f"""
    <style>
      [data-testid="stToolbar"] {{ display: none; }}
      [data-testid="stHeader"] {{ display: none; }}
      [data-testid="stAppViewContainer"] > .main > .block-container,
      .block-container {{
        max-width: {2 * CROPPER_HEIGHT + GAP_PX + 32}px;
        padding: 1rem 1rem 1rem 1rem;
      }}
      .section-header {{
        margin: 1rem 0 0.25rem 0;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.6;
      }}
      [data-testid="stHorizontalBlock"]:has(iframe),
      [data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) {{
        gap: {GAP_PX}px;
        flex-wrap: nowrap;
        justify-content: flex-start;
      }}
      [data-testid="stHorizontalBlock"]:has(iframe) > [data-testid="stColumn"]:nth-child(1) {{
        flex: 0 0 calc(50% - {GAP_PX // 2}px);
        max-width: {CROPPER_HEIGHT}px;
        min-width: 0;
      }}
      [data-testid="stHorizontalBlock"]:has(iframe) > [data-testid="stColumn"]:nth-child(2) {{
        flex: 0 0 calc(25% - {GAP_PX // 4 + GAP_PX // 2}px);
        max-width: {PREVIEW_HEIGHT}px;
        min-width: 0;
      }}
      [data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) > [data-testid="stColumn"] {{
        flex: 0 0 calc(37.5% - {(GAP_PX // 2 + GAP_PX // 4 + GAP_PX // 2) // 2}px);
        max-width: {(CROPPER_HEIGHT + PREVIEW_HEIGHT) // 2}px;
        min-width: 0;
      }}
      [data-testid="stHorizontalBlock"]:has(iframe) > [data-testid="stColumn"]:nth-child(2) > [data-testid="stVerticalBlock"] {{
        gap: {GAP_PX}px;
      }}
      [data-testid="stHorizontalBlock"]:has(iframe) > [data-testid="stColumn"]:nth-child(1) iframe {{
        border-radius: 8px;
      }}
      [data-testid="stFileUploaderDropzone"] {{
        flex-direction: row !important;
        align-items: center !important;
        height: 84px !important;
        box-sizing: border-box;
      }}
      [data-testid="stFileUploaderDropzone"] button {{
        min-width: 120px;
      }}
      [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .section-header-sel),
      [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .section-header-ud) {{
        gap: 0.25rem;
      }}
      [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .section-header-sel) [data-testid="stHorizontalBlock"] {{
        flex-wrap: nowrap;
      }}
      [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .section-header-sel) > :nth-child(2),
      [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .section-header-ud) > :nth-child(2) {{
        margin-top: 0.75rem;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Image Rotate & Mirror")


def section(col, label, name=""):
    extra = f" section-header-{name}" if name else ""
    col.markdown(f'<div class="section-header{extra}">{label}</div>', unsafe_allow_html=True)


def _inline_label(container, label):
    lcol, icol = container.columns([1, 4])
    lcol.markdown(
        f'<div style="padding-top: 0.5rem; font-size: 0.95rem;">{label}</div>',
        unsafe_allow_html=True,
    )
    return icol


top_left, top_right = st.columns(2)
mid_left, mid_right = st.columns(2)
sel_container = mid_left.container()

section(mid_right, "Upload / Download image", "ud")
uploaded = mid_right.file_uploader(
    "Upload image",
    type=["png", "jpg", "jpeg", "webp"],
    label_visibility="collapsed",
)
if uploaded is not None:
    upload_key = getattr(uploaded, "file_id", uploaded.name)
    upload_name = uploaded.name
else:
    upload_key = DEFAULT_IMAGE
    upload_name = DEFAULT_IMAGE.rsplit("/", 1)[-1]

if st.session_state.get("upload_key") != upload_key:
    st.session_state["upload_key"] = upload_key
    st.session_state.pop("box_x", None)
    st.session_state.pop("box_y", None)
    st.session_state.pop("box_size", None)
    st.session_state["_fabric_scale_x"] = 1.0
    st.session_state.pop("_prev_cropper", None)
    loaded = Image.open(uploaded if uploaded is not None else DEFAULT_IMAGE)
    if loaded.mode not in ("RGB", "RGBA"):
        loaded = loaded.convert("RGB")
    st.session_state["_img"] = loaded
img = st.session_state["_img"]

if "_rotation_in" not in st.session_state:
    st.session_state["_rotation_in"] = DEFAULT_ROTATION
rotation = st.session_state["_rotation_in"]

rot_key = (upload_key, rotation)
if st.session_state.get("_rot_key") != rot_key:
    st.session_state["_rot_key"] = rot_key
    st.session_state["_full_rotated"] = rotate_full(img, rotation)
full_rotated = st.session_state["_full_rotated"]

max_size = min(full_rotated.width, full_rotated.height)
max_size -= max_size % 2
min_size = min(MIN_SELECTION, max(2, max_size))

canvas_w = canvas_h = CROPPER_HEIGHT

display_scale = min(canvas_w / full_rotated.width, canvas_h / full_rotated.height)
display_img_w = max(1, round(full_rotated.width * display_scale))
display_img_h = max(1, round(full_rotated.height * display_scale))
offset_x = (canvas_w - display_img_w) // 2
offset_y = (canvas_h - display_img_h) // 2

scale_x = st.session_state.setdefault("_fabric_scale_x", 1.0)
cropper_key = f"_cropper_{upload_key}"

cropper_value = st.session_state.get(cropper_key)
prev_cropper = st.session_state.get("_prev_cropper")
if (
    cropper_value
    and cropper_value != prev_cropper
    and isinstance(cropper_value, dict)
    and "coords" in cropper_value
):
    coords = cropper_value["coords"]
    st.session_state["box_x"] = round((int(coords["left"]) - offset_x) / display_scale)
    st.session_state["box_y"] = round((int(coords["top"]) - offset_y) / display_scale)
    cur_w = float(coords["width"])
    visible = round(int(st.session_state.get("box_size", 0)) * display_scale)
    last_sent = round(visible / scale_x) if scale_x > 0 else visible
    stroke_eff_old = CROPPER_STROKE / scale_x if scale_x > 0 else CROPPER_STROKE
    expected_w = (last_sent + stroke_eff_old) * scale_x
    if abs(cur_w - expected_w) > 1:
        new_scale_x = cur_w / (last_sent + stroke_eff_old)
        new_size = round(last_sent * new_scale_x / display_scale)
        st.session_state["box_size"] = new_size - new_size % 2
        st.session_state["_fabric_scale_x"] = new_scale_x
        scale_x = new_scale_x
st.session_state["_prev_cropper"] = cropper_value

if "box_size" not in st.session_state:
    st.session_state["box_size"] = max_size // 2
size = max(min_size, min(max_size, int(st.session_state["box_size"])))
size -= size % 2
st.session_state["box_size"] = size

if "box_x" not in st.session_state:
    st.session_state["box_x"] = (full_rotated.width - size) // 2
if "box_y" not in st.session_state:
    st.session_state["box_y"] = (full_rotated.height - size) // 2
left = max(0, min(full_rotated.width - size, int(st.session_state["box_x"])))
top = max(0, min(full_rotated.height - size, int(st.session_state["box_y"])))
st.session_state["box_x"] = left
st.session_state["box_y"] = top


def _sync_size():
    val = int(st.session_state["_box_size_in"])
    new_size = val - val % 2
    old_size = int(st.session_state.get("box_size", new_size))
    shift = (new_size - old_size) // 2
    st.session_state["box_size"] = new_size
    if shift:
        st.session_state["box_x"] = int(st.session_state.get("box_x", 0)) - shift
        st.session_state["box_y"] = int(st.session_state.get("box_y", 0)) - shift


def _sync_x():
    st.session_state["box_x"] = int(st.session_state["_box_x_in"])


def _sync_y():
    st.session_state["box_y"] = int(st.session_state["_box_y_in"])


st.session_state["_box_size_in"] = size
st.session_state["_box_x_in"] = left
st.session_state["_box_y_in"] = top

section(sel_container, "Selection Area", "sel")

_inline_label(sel_container, "Size").number_input(
    "Size",
    min_value=min_size,
    max_value=max_size,
    step=2,
    key="_box_size_in",
    on_change=_sync_size,
    label_visibility="collapsed",
)
_inline_label(sel_container, "X").number_input(
    "X",
    min_value=0,
    max_value=full_rotated.width - size,
    step=1,
    key="_box_x_in",
    on_change=_sync_x,
    label_visibility="collapsed",
)
_inline_label(sel_container, "Y").number_input(
    "Y",
    min_value=0,
    max_value=full_rotated.height - size,
    step=1,
    key="_box_y_in",
    on_change=_sync_y,
    label_visibility="collapsed",
)
_inline_label(sel_container, "Rotation").number_input(
    "Rotation",
    min_value=ROTATION_MIN,
    max_value=ROTATION_MAX,
    step=ROTATION_STEP,
    key="_rotation_in",
    label_visibility="collapsed",
)

display_img = full_rotated.resize((display_img_w, display_img_h), Image.Resampling.LANCZOS)
placeholder = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
disp_left = round(left * display_scale) + offset_x
disp_top = round(top * display_scale) + offset_y
visible = round(size * display_scale)
disp_size = round(visible / scale_x) if scale_x > 0 else visible
stroke_eff = CROPPER_STROKE / scale_x if scale_x > 0 else CROPPER_STROKE

bg_image = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
bg_image.alpha_composite(
    display_img if display_img.mode == "RGBA" else display_img.convert("RGBA"),
    (offset_x, offset_y),
)

with top_left:
    st_cropper(
        placeholder,  # type: ignore[arg-type]
        realtime_update=True,
        box_color=CROPPER_BOX_COLOR,
        aspect_ratio=(1, 1),
        return_type="box",
        default_coords=(
            disp_left,
            disp_left + disp_size,
            disp_top,
            disp_top + disp_size,
        ),
        should_resize_image=False,
        stroke_width=stroke_eff,
        key=cropper_key,
    )

bg_b64 = _png_b64(bg_image)
dim_alpha_css = round(DIM_ALPHA / 255 * 1000) / 1000
top_left.html(
    f"""
    <script>
    (function() {{
      const url = 'data:image/png;base64,{bg_b64}';
      const pos = '0 0';
      const canvasW = {canvas_w};
      const canvasH = {canvas_h};
      const holeLeft0 = {disp_left};
      const holeTop0 = {disp_top};
      const holeSize0 = {visible};
      const dimAlpha = {dim_alpha_css};
      const findIframe = () => {{
        const iframes = Array.from(document.querySelectorAll('iframe'));
        return iframes.find(f => {{
          try {{ return f.contentDocument && f.contentDocument.querySelector('canvas'); }}
          catch (e) {{ return false; }}
        }});
      }};
      const updateScale = () => {{
        const iframe = findIframe();
        if (!iframe || !iframe.contentDocument || !iframe.contentDocument.body) return;
        const body = iframe.contentDocument.body;
        const parent = iframe.parentElement;
        const availW = parent ? parent.getBoundingClientRect().width : canvasW;
        const sc = Math.min(1, availW / canvasW) || 1;
        iframe.style.width = (canvasW * sc) + 'px';
        iframe.style.height = (canvasH * sc) + 'px';
        body.style.transformOrigin = 'top left';
        body.style.transform = sc < 1 ? `scale(${{sc}})` : '';
        const upperEl = body.querySelector('canvas[data-fabric="top"]');
        if (upperEl) upperEl.__scale = sc;
      }};
      const apply = () => {{
        try {{
          const iframe = findIframe();
          if (!iframe) {{ requestAnimationFrame(apply); return; }}
          const idoc = iframe.contentDocument;
          const body = idoc.body;
          if (!body) {{ requestAnimationFrame(apply); return; }}
          body.style.margin = '0';
          body.style.width = canvasW + 'px';
          body.style.height = canvasH + 'px';
          body.style.overflow = 'hidden';
          if (idoc.documentElement) idoc.documentElement.style.overflow = 'hidden';
          const checkerTile = {CHECKER_CELL * 2};
          body.style.backgroundColor = '{CHECKER_LIGHT}';
          body.style.backgroundImage = `url("${{url}}"), conic-gradient({CHECKER_DARK} 25%, {CHECKER_LIGHT} 0 50%, {CHECKER_DARK} 0 75%, {CHECKER_LIGHT} 0)`;
          body.style.backgroundRepeat = 'no-repeat, repeat';
          body.style.backgroundPosition = pos + ', 0 0';
          body.style.backgroundSize = `auto, ${{checkerTile}}px ${{checkerTile}}px`;
          if (!body.style.position) body.style.position = 'relative';

          let hole = idoc.getElementById('dim-hole');
          if (!hole) {{
            hole = idoc.createElement('div');
            hole.id = 'dim-hole';
            hole.style.position = 'absolute';
            hole.style.pointerEvents = 'none';
            hole.style.zIndex = '0';
            body.insertBefore(hole, body.firstChild);
          }}
          hole.style.boxShadow = `0 0 0 99999px rgba(0,0,0,${{dimAlpha}})`;

          const SPLIT_W = 2;
          let split = idoc.getElementById('split-line');
          if (!split) {{
            split = idoc.createElement('div');
            split.id = 'split-line';
            split.style.position = 'absolute';
            split.style.pointerEvents = 'none';
            split.style.width = SPLIT_W + 'px';
            split.style.backgroundColor = '{CROPPER_BOX_COLOR}';
            split.style.zIndex = '0';
            body.insertBefore(split, body.firstChild);
          }}

          const setBox = (l, t, s) => {{
            hole.style.left = l + 'px';
            hole.style.top = t + 'px';
            hole.style.width = s + 'px';
            hole.style.height = s + 'px';
            split.style.left = (l + s / 2 - SPLIT_W / 2) + 'px';
            split.style.top = t + 'px';
            split.style.height = s + 'px';
          }};
          setBox(holeLeft0, holeTop0, holeSize0);
          hole.style.display = '';
          split.style.display = '';

          updateScale();
          if (window.__cropperResizeListener) {{
            window.removeEventListener('resize', window.__cropperResizeListener);
          }}
          window.__cropperResizeListener = () => {{ requestAnimationFrame(updateScale); }};
          window.addEventListener('resize', window.__cropperResizeListener);

          const upper = body.querySelector('canvas[data-fabric="top"]');
          if (upper && !upper.__dimHooked) {{
            upper.__dimHooked = true;
            const HANDLE_PAD = 6;
            upper.addEventListener('pointerdown', (ev) => {{
              const sc = upper.__scale || 1;
              const r = upper.getBoundingClientRect();
              const mx = (ev.clientX - r.left) / sc;
              const my = (ev.clientY - r.top) / sc;
              const hL = parseFloat(hole.style.left);
              const hT = parseFloat(hole.style.top);
              const hS = parseFloat(hole.style.width);
              const hR = hL + hS;
              const hB = hT + hS;
              const hcx = (hL + hR) / 2;
              const hcy = (hT + hB) / 2;
              const handles = [
                [hL, hT], [hR, hT], [hL, hB], [hR, hB],
                [hcx, hT], [hcx, hB], [hL, hcy], [hR, hcy],
              ];
              const onHandle = handles.some(([hx, hy]) =>
                Math.abs(mx - hx) < HANDLE_PAD && Math.abs(my - hy) < HANDLE_PAD);
              const inside = mx >= hL && mx <= hR && my >= hT && my <= hB;
              const pid = ev.pointerId;
              if (onHandle) {{
                try {{ upper.setPointerCapture(pid); }} catch (e) {{}}
                hole.style.display = 'none';
                split.style.display = 'none';
                const onUp = (e) => {{
                  if (e.pointerId !== pid) return;
                  upper.removeEventListener('pointerup', onUp);
                  upper.removeEventListener('pointercancel', onUp);
                }};
                upper.addEventListener('pointerup', onUp);
                upper.addEventListener('pointercancel', onUp);
                return;
              }}
              if (!inside) return;
              try {{ upper.setPointerCapture(pid); }} catch (e) {{}}
              const startMx = mx, startMy = my;
              const startL = hL, startT = hT;
              const onMove = (e) => {{
                if (e.pointerId !== pid) return;
                const sc2 = upper.__scale || 1;
                const r2 = upper.getBoundingClientRect();
                const mx2 = (e.clientX - r2.left) / sc2;
                const my2 = (e.clientY - r2.top) / sc2;
                setBox(startL + (mx2 - startMx), startT + (my2 - startMy), hS);
              }};
              const onUp = (e) => {{
                if (e.pointerId !== pid) return;
                upper.removeEventListener('pointermove', onMove);
                upper.removeEventListener('pointerup', onUp);
                upper.removeEventListener('pointercancel', onUp);
              }};
              upper.addEventListener('pointermove', onMove);
              upper.addEventListener('pointerup', onUp);
              upper.addEventListener('pointercancel', onUp);
            }});
          }}
        }} catch (e) {{ requestAnimationFrame(apply); }}
      }};
      apply();
    }})();
    </script>
    """,
    unsafe_allow_javascript=True,
)

region = full_rotated.crop((left, top, left + size, top + size))
left_out, right_out = mirror_pair(region)

preview_left = left_out.resize(
    (max(1, round(left_out.width * PREVIEW_HEIGHT / left_out.height)), PREVIEW_HEIGHT),
    Image.Resampling.LANCZOS,
)
preview_right = right_out.resize(
    (max(1, round(right_out.width * PREVIEW_HEIGHT / right_out.height)), PREVIEW_HEIGHT),
    Image.Resampling.LANCZOS,
)

top_right.image(preview_left, width="stretch")
top_right.image(preview_right, width="stretch")


stem = upload_name.rsplit(".", 1)[0]
left_b64 = _png_b64(left_out)
right_b64 = _png_b64(right_out)
left_name = f"{stem}_left.png"
right_name = f"{stem}_right.png"

mid_right.html(
    f"""
    <style>
      html, body {{ margin: 0; background: transparent; font-family: 'Source Sans', 'Source Sans Pro', sans-serif; color: rgb(250, 250, 250); }}
      .dl-dropzone {{
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 12px;
        padding: 12px;
        height: 84px;
        box-sizing: border-box;
        border-radius: 0.5rem;
        background-color: rgb(38, 39, 48);
      }}
      .dl-button {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        min-width: 120px;
        height: 40px;
        padding: 6px 12px;
        box-sizing: border-box;
        border: 1px solid rgba(250, 250, 250, 0.2);
        border-radius: 0.5rem;
        background: transparent;
        color: rgb(250, 250, 250);
        font-size: 1rem;
        line-height: 25.6px;
        font-family: inherit;
        cursor: pointer;
        transition: border-color 120ms ease, color 120ms ease;
      }}
      .dl-button:hover {{
        border-color: rgb(255, 75, 75);
        color: rgb(255, 75, 75);
      }}
      .dl-icon {{
        font-family: 'Material Symbols Rounded';
        font-size: 20px;
        line-height: 20px;
        font-weight: 400;
        text-transform: none;
        letter-spacing: normal;
        font-feature-settings: 'liga';
      }}
      .dl-info {{
        font-size: 14px;
        line-height: 22.4px;
        color: rgba(250, 250, 250, 0.6);
      }}
    </style>
    <div class="dl-dropzone">
      <button id="dl-both" class="dl-button"><span class="dl-icon">download</span><span>Download</span></button>
      <div class="dl-info">Save left + right images as PNG</div>
    </div>
    <script>
    (function() {{
      const dl = (b64, name) => {{
        const a = document.createElement('a');
        a.href = 'data:image/png;base64,' + b64;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }};
      document.getElementById('dl-both').onclick = function() {{
        dl({json.dumps(left_b64)}, {json.dumps(left_name)});
        setTimeout(() => dl({json.dumps(right_b64)}, {json.dumps(right_name)}), 150);
      }};
    }})();
    </script>
    """,
    unsafe_allow_javascript=True,
)
