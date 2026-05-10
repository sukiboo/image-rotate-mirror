import streamlit as st
from PIL import Image

from src import cropper_overlay, download_button, state
from src.constants import (
    DEFAULT_IMAGE,
    MIN_SELECTION,
    PREVIEW_HEIGHT,
    ROTATION_MAX,
    ROTATION_MIN,
    ROTATION_STEP,
)
from src.mirror import mirror_pair
from src.styles import STYLES
from src.widgets import inline_label, section


def main():
    st.set_page_config(page_title="Image Rotate & Mirror", layout="wide")
    st.markdown(STYLES, unsafe_allow_html=True)
    st.title("Image Rotate & Mirror")

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

    img = state.load_image(uploaded, upload_key)
    rotation = state.get_rotation()
    full_rotated = state.cache_rotation(img, upload_key, rotation)

    max_size = min(full_rotated.width, full_rotated.height)
    max_size -= max_size % 2
    min_size = min(MIN_SELECTION, max(2, max_size))

    geom = cropper_overlay.geometry(full_rotated)
    scale_x = st.session_state.setdefault("_fabric_scale_x", 1.0)
    cropper_key = f"_cropper_{upload_key}"

    scale_x = state.apply_cropper_changes(
        cropper_key, scale_x, geom.display_scale, geom.offset_x, geom.offset_y
    )
    size, left, top = state.normalize_box(full_rotated, min_size, max_size)

    st.session_state["_box_size_in"] = size
    st.session_state["_box_x_in"] = left
    st.session_state["_box_y_in"] = top

    section(sel_container, "Selection Area", "sel")

    inline_label(sel_container, "Size").number_input(
        "Size",
        min_value=min_size,
        max_value=max_size,
        step=2,
        key="_box_size_in",
        on_change=state.sync_size,
        label_visibility="collapsed",
    )
    inline_label(sel_container, "X").number_input(
        "X",
        min_value=0,
        max_value=full_rotated.width - size,
        step=1,
        key="_box_x_in",
        on_change=state.sync_x,
        label_visibility="collapsed",
    )
    inline_label(sel_container, "Y").number_input(
        "Y",
        min_value=0,
        max_value=full_rotated.height - size,
        step=1,
        key="_box_y_in",
        on_change=state.sync_y,
        label_visibility="collapsed",
    )
    inline_label(sel_container, "Rotation").number_input(
        "Rotation",
        min_value=ROTATION_MIN,
        max_value=ROTATION_MAX,
        step=ROTATION_STEP,
        key="_rotation_in",
        label_visibility="collapsed",
    )

    cropper_overlay.render(top_left, full_rotated, geom, size, left, top, scale_x, cropper_key)

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

    download_button.render(mid_right, left_out, right_out, upload_name)
