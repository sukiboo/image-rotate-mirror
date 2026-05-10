import json

from src.utils import png_b64


def render(container, left_out, right_out, upload_name):
    stem = upload_name.rsplit(".", 1)[0]
    left_b64 = png_b64(left_out)
    right_b64 = png_b64(right_out)
    left_name = f"{stem}_left.png"
    right_name = f"{stem}_right.png"
    container.html(
        _download_html(left_b64, right_b64, left_name, right_name), unsafe_allow_javascript=True
    )


def _download_html(left_b64, right_b64, left_name, right_name):
    return f"""
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
    """
