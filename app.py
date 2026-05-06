import base64
import io
import json

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from streamlit_cropper import st_cropper

from mirror import mirror_pair, rotate

ROTATION_MIN = -180.0
ROTATION_MAX = 180.0
ROTATION_STEP = 0.5
DEFAULT_ROTATION = 0.0
MIN_SELECTION = 32

st.set_page_config(page_title="Image Rotate & Mirror", layout="wide")
st.title("Image Rotate & Mirror")

uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"])
if uploaded is None:
    st.info("Upload an image to begin.")
    st.stop()

img = Image.open(uploaded)
if img.mode not in ("RGB", "RGBA"):
    img = img.convert("RGB")

upload_key = getattr(uploaded, "file_id", uploaded.name)
if st.session_state.get("upload_key") != upload_key:
    st.session_state["upload_key"] = upload_key
    st.session_state.pop("box_center", None)
    st.session_state.pop("box_size", None)

img_col, ctrl_col = st.columns([3, 1])

rotation = ctrl_col.slider(
    "Rotation (°)", ROTATION_MIN, ROTATION_MAX, DEFAULT_ROTATION, ROTATION_STEP
)

rotated = rotate(img, rotation)
max_size = min(rotated.width, rotated.height)
min_size = min(MIN_SELECTION, max(1, max_size - 1))

prev_size = st.session_state.get("box_size", max_size // 2)
default_size = max(min_size, min(prev_size, max_size))
size = ctrl_col.slider("Selection size", min_size, max_size, default_size, 1)
st.session_state["box_size"] = size

cx, cy = st.session_state.get("box_center", (rotated.width // 2, rotated.height // 2))
half = size // 2
cx = max(half, min(rotated.width - (size - half), cx))
cy = max(half, min(rotated.height - (size - half), cy))
left = cx - half
top = cy - half
right = left + size
bottom = top + size

with img_col:
    box = st_cropper(
        rotated,
        realtime_update=True,
        box_color="#3B82F6",
        aspect_ratio=(1, 1),
        return_type="box",
        default_coords=(left, right, top, bottom),
    )

st.session_state["box_center"] = (
    box["left"] + box["width"] // 2,
    box["top"] + box["height"] // 2,
)

region = rotated.crop(
    (box["left"], box["top"], box["left"] + box["width"], box["top"] + box["height"])
)
left_out, right_out = mirror_pair(region)

prev_left, prev_right = st.columns(2)
prev_left.image(left_out, caption="<A | A>", use_container_width=True)
prev_right.image(right_out, caption="<B | B>", use_container_width=True)


def _png_b64(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


stem = uploaded.name.rsplit(".", 1)[0]
left_b64 = _png_b64(left_out)
right_b64 = _png_b64(right_out)
left_name = f"{stem}_left.png"
right_name = f"{stem}_right.png"

components.html(
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
    height=70,
)
