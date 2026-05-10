def section(col, label, name=""):
    extra = f" section-header-{name}" if name else ""
    col.markdown(f'<div class="section-header{extra}">{label}</div>', unsafe_allow_html=True)


def inline_label(container, label):
    lcol, icol = container.columns([1, 4])
    lcol.markdown(
        f'<div style="padding-top: 0.5rem; font-size: 0.95rem;">{label}</div>',
        unsafe_allow_html=True,
    )
    return icol
