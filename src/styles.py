from src.constants import CROPPER_HEIGHT, GAP_PX, PREVIEW_HEIGHT

STYLES = f"""
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
"""
