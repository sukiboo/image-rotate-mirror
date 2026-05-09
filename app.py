import base64
import io
import json

import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper

from mirror import mirror_pair, rotate_full

ROTATION_MIN = -45.0
ROTATION_MAX = 45.0
ROTATION_STEP = 1.0
DEFAULT_ROTATION = 0.0
MIN_SELECTION = 32
DEFAULT_IMAGE = "images/cow.jpeg"
CROPPER_HEIGHT = 512
PREVIEW_HEIGHT = 256
CROPPER_STROKE = 3
CROPPER_BG_COLOR = "#1f2937"


def _png_b64(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


st.set_page_config(page_title="Image Rotate & Mirror", layout="wide")
st.title("Image Rotate & Mirror")

img_col, ctrl_col = st.columns([3, 1])

uploaded = ctrl_col.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"])
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

rotation = ctrl_col.slider(
    "Rotation (°)", ROTATION_MIN, ROTATION_MAX, DEFAULT_ROTATION, ROTATION_STEP
)

rot_key = (upload_key, rotation)
if st.session_state.get("_rot_key") != rot_key:
    st.session_state["_rot_key"] = rot_key
    st.session_state["_full_rotated"] = rotate_full(img, rotation)
full_rotated = st.session_state["_full_rotated"]

max_size = min(full_rotated.width, full_rotated.height)
max_size -= max_size % 2
min_size = min(MIN_SELECTION, max(2, max_size))

unit_scale = CROPPER_HEIGHT / img.height
canvas_w = max(1, round(img.width * unit_scale))
canvas_h = CROPPER_HEIGHT
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
    expected_w = (last_sent + CROPPER_STROKE) * scale_x
    if abs(cur_w - expected_w) > 1:
        new_scale_x = cur_w / (last_sent + CROPPER_STROKE)
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
    st.session_state["box_size"] = val - val % 2


def _sync_x():
    st.session_state["box_x"] = int(st.session_state["_box_x_in"])


def _sync_y():
    st.session_state["box_y"] = int(st.session_state["_box_y_in"])


st.session_state["_box_size_in"] = size
st.session_state["_box_x_in"] = left
st.session_state["_box_y_in"] = top

ctrl_col.number_input(
    "Selection size",
    min_value=min_size,
    max_value=max_size,
    step=2,
    key="_box_size_in",
    on_change=_sync_size,
)
ctrl_col.number_input(
    "X",
    min_value=0,
    max_value=full_rotated.width - size,
    step=1,
    key="_box_x_in",
    on_change=_sync_x,
)
ctrl_col.number_input(
    "Y",
    min_value=0,
    max_value=full_rotated.height - size,
    step=1,
    key="_box_y_in",
    on_change=_sync_y,
)

display_img = full_rotated.resize((display_img_w, display_img_h), Image.Resampling.LANCZOS)
placeholder = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
disp_left = round(left * display_scale) + offset_x
disp_top = round(top * display_scale) + offset_y
visible = round(size * display_scale)
disp_size = round(visible / scale_x) if scale_x > 0 else visible

with img_col:
    st_cropper(
        placeholder,  # type: ignore[arg-type]
        realtime_update=True,
        box_color="#3B82F6",
        aspect_ratio=(1, 1),
        return_type="box",
        default_coords=(
            disp_left,
            disp_left + disp_size,
            disp_top,
            disp_top + disp_size,
        ),
        should_resize_image=False,
        stroke_width=CROPPER_STROKE,
        key=cropper_key,
    )

display_img_b64 = _png_b64(display_img)
img_col.html(
    f"""
    <script>
    (function() {{
      const url = 'data:image/png;base64,{display_img_b64}';
      const pos = '{offset_x}px {offset_y}px';
      const apply = () => {{
        try {{
          const iframes = Array.from(document.querySelectorAll('iframe'));
          const iframe = iframes.find(f => {{
            try {{ return f.contentDocument && f.contentDocument.querySelector('canvas'); }}
            catch (e) {{ return false; }}
          }});
          if (!iframe) {{ requestAnimationFrame(apply); return; }}
          const body = iframe.contentDocument.body;
          if (!body) {{ requestAnimationFrame(apply); return; }}
          iframe.style.width = '{canvas_w}px';
          iframe.style.height = '{canvas_h}px';
          body.style.margin = '0';
          body.style.width = '{canvas_w}px';
          body.style.height = '{canvas_h}px';
          body.style.backgroundColor = '{CROPPER_BG_COLOR}';
          body.style.backgroundImage = `url("${{url}}")`;
          body.style.backgroundRepeat = 'no-repeat';
          body.style.backgroundPosition = pos;
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

p1, p2, _ = img_col.columns([1, 1, 2])
p1.image(preview_left, width="content")
p2.image(preview_right, width="content")


stem = upload_name.rsplit(".", 1)[0]
left_b64 = _png_b64(left_out)
right_b64 = _png_b64(right_out)
left_name = f"{stem}_left.png"
right_name = f"{stem}_right.png"

ctrl_col.html(
    f"""
    <div style="text-align:center; padding-top:0.5rem;">
      <button id="dl-both" style="
          padding: 0.5rem 1.5rem;
          border: 1px solid rgba(49,51,63,0.2);
          border-radius: 0.5rem;
          background: #ffffff;
          color: #31333F;
          font-size: 1rem;
          font-family: inherit;
          cursor: pointer;
      ">Download both</button>
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
