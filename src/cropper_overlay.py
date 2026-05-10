from collections import namedtuple

from PIL import Image
from streamlit_cropper import st_cropper

from src.constants import (
    CHECKER_CELL,
    CHECKER_DARK,
    CHECKER_LIGHT,
    CROPPER_BOX_COLOR,
    CROPPER_HEIGHT,
    CROPPER_STROKE,
    DIM_ALPHA,
)
from src.utils import png_b64

Geometry = namedtuple(
    "Geometry",
    "canvas_w canvas_h display_scale offset_x offset_y display_img_w display_img_h",
)


def geometry(full_rotated):
    canvas_w = canvas_h = CROPPER_HEIGHT
    display_scale = min(canvas_w / full_rotated.width, canvas_h / full_rotated.height)
    display_img_w = max(1, round(full_rotated.width * display_scale))
    display_img_h = max(1, round(full_rotated.height * display_scale))
    offset_x = (canvas_w - display_img_w) // 2
    offset_y = (canvas_h - display_img_h) // 2
    return Geometry(
        canvas_w, canvas_h, display_scale, offset_x, offset_y, display_img_w, display_img_h
    )


def render(container, full_rotated, geom, size, left, top, scale_x, cropper_key):
    display_img = full_rotated.resize(
        (geom.display_img_w, geom.display_img_h), Image.Resampling.LANCZOS
    )
    placeholder = Image.new("RGBA", (geom.canvas_w, geom.canvas_h), (0, 0, 0, 0))
    disp_left = round(left * geom.display_scale) + geom.offset_x
    disp_top = round(top * geom.display_scale) + geom.offset_y
    visible = round(size * geom.display_scale)
    disp_size = round(visible / scale_x) if scale_x > 0 else visible
    stroke_eff = CROPPER_STROKE / scale_x if scale_x > 0 else CROPPER_STROKE

    bg_image = Image.new("RGBA", (geom.canvas_w, geom.canvas_h), (0, 0, 0, 0))
    bg_image.alpha_composite(
        display_img if display_img.mode == "RGBA" else display_img.convert("RGBA"),
        (geom.offset_x, geom.offset_y),
    )

    with container:
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

    bg_b64 = png_b64(bg_image)
    dim_alpha_css = round(DIM_ALPHA / 255 * 1000) / 1000
    container.html(
        _overlay_script(
            bg_b64, geom.canvas_w, geom.canvas_h, disp_left, disp_top, visible, dim_alpha_css
        ),
        unsafe_allow_javascript=True,
    )


def _overlay_script(bg_b64, canvas_w, canvas_h, disp_left, disp_top, visible, dim_alpha_css):
    return f"""
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
    """
