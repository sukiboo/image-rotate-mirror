import streamlit as st
from PIL import Image

from src.constants import CROPPER_STROKE, DEFAULT_IMAGE, DEFAULT_ROTATION
from src.mirror import rotate_full


def load_image(uploaded, upload_key):
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
    return st.session_state["_img"]


def get_rotation():
    if "_rotation_in" not in st.session_state:
        st.session_state["_rotation_in"] = DEFAULT_ROTATION
    return st.session_state["_rotation_in"]


def cache_rotation(img, upload_key, rotation):
    rot_key = (upload_key, rotation)
    if st.session_state.get("_rot_key") != rot_key:
        st.session_state["_rot_key"] = rot_key
        st.session_state["_full_rotated"] = rotate_full(img, rotation)
    return st.session_state["_full_rotated"]


def apply_cropper_changes(cropper_key, scale_x, display_scale, offset_x, offset_y):
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
    return scale_x


def normalize_box(full_rotated, min_size, max_size):
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
    return size, left, top


def sync_size():
    val = int(st.session_state["_box_size_in"])
    new_size = val - val % 2
    old_size = int(st.session_state.get("box_size", new_size))
    shift = (new_size - old_size) // 2
    st.session_state["box_size"] = new_size
    if shift:
        st.session_state["box_x"] = int(st.session_state.get("box_x", 0)) - shift
        st.session_state["box_y"] = int(st.session_state.get("box_y", 0)) - shift


def sync_x():
    st.session_state["box_x"] = int(st.session_state["_box_x_in"])


def sync_y():
    st.session_state["box_y"] = int(st.session_state["_box_y_in"])
