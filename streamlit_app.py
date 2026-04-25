import base64
import html
from io import BytesIO

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from classify import classify_image, is_stub_mode
from location import geocode_address, get_location_from_exif
from routing import get_guide
from storage import load_image, load_pins, save_pin

NYC_CENTER = [40.7128, -74.0060]

CATEGORY_COLORS = {
    "curbside_trash": "#16a34a",
    "overflowing_basket": "#16a34a",
    "park_trash": "#16a34a",
    "bulk_item": "#eab308",
    "illegal_dumping": "#eab308",
    "dog_waste": "#dc2626",
    "dead_animal": "#dc2626",
    "tree_damage": "#dc2626",
    "broken_sidewalk": "#ea580c",
    "pothole": "#ea580c",
    "damaged_sign": "#ea580c",
    "broken_streetlight": "#ea580c",
    "graffiti": "#ea580c",
    "abandoned_vehicle": "#ea580c",
    "other": "#ffffff",
}


def _thumbnail(image_bytes: bytes, max_size: int = 400) -> bytes:
    img = Image.open(BytesIO(image_bytes))
    img.thumbnail((max_size, max_size))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def _build_folium_map() -> folium.Map:
    pins = load_pins()
    m = folium.Map(location=NYC_CENTER, zoom_start=11, tiles="cartodbpositron")
    m.get_root().header.add_child(folium.Element(
        "<style>html,body{height:100%!important;margin:0!important;overflow:hidden!important;}"
        ".folium-map,#" + m.get_name() + "{height:100vh!important;width:100vw!important;}</style>"
    ))
    for pin in pins:
        image_bytes = load_image(pin["image"])
        if image_bytes is None:
            folium.Marker(
                [pin["lat"], pin["lng"]],
                popup=folium.Popup(f"<b>{pin['display_name']}</b>", max_width=260),
                tooltip=pin["display_name"],
            ).add_to(m)
            continue

        thumb_b64 = base64.b64encode(_thumbnail(image_bytes)).decode("utf-8")
        display_name = html.escape(pin.get("display_name", ""))
        reasoning = html.escape(pin.get("reasoning", ""))
        notable_details = html.escape(pin.get("notable_details", ""))
        confidence = html.escape(pin.get("confidence", ""))

        reasoning_html = (
            f"<div style='margin-top:6px;font-size:12px;color:#333;line-height:1.3'>{reasoning}</div>"
            if reasoning
            else ""
        )
        details_html = (
            f"<div style='margin-top:4px;font-size:11px;color:#555;line-height:1.3'>"
            f"<b>Details:</b> {notable_details}</div>"
            if notable_details
            else ""
        )
        confidence_html = (
            f"<div style='margin-top:4px;font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.03em'>"
            f"Confidence: {confidence}</div>"
            if confidence
            else ""
        )
        popup_html = (
            f"<div style='font-family:sans-serif;max-width:240px'>"
            f"<div style='font-weight:600;font-size:13px;margin-bottom:4px'>{display_name}</div>"
            f"<img src='data:image/jpeg;base64,{thumb_b64}' width='220' style='border-radius:4px;display:block'>"
            f"{reasoning_html}"
            f"{details_html}"
            f"{confidence_html}"
            f"</div>"
        )
        border_color = CATEGORY_COLORS.get(pin.get("category", ""), "#ffffff")
        icon_html = (
            f"<div style=\""
            f"width:48px;height:48px;border-radius:50%;"
            f"border:3px solid {border_color};box-shadow:0 2px 6px rgba(0,0,0,0.35);"
            f"background-image:url('data:image/jpeg;base64,{thumb_b64}');"
            f"background-size:cover;background-position:center;"
            f"\"></div>"
        )
        folium.Marker(
            [pin["lat"], pin["lng"]],
            icon=folium.DivIcon(html=icon_html, icon_size=(48, 48), icon_anchor=(24, 24)),
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=pin["display_name"],
        ).add_to(m)
    return m


def _render_upload_panel(key_prefix: str) -> None:
    st.title("TrashAI")
    st.caption("Snap a photo of anything needing civic action in NYC. We'll tell you exactly where and how to report it.")
    if is_stub_mode():
        st.warning("⚙️ Stub mode: Claude Vision is disabled. Add your API key to `.streamlit/secrets.toml` to enable real classification.")
    pin_count = len(load_pins())
    st.caption(f"📍 {pin_count} pinned on the map")

    uploaded = st.file_uploader(
        "Upload a photo",
        type=["jpg", "jpeg", "png"],
        key=f"{key_prefix}_file",
    )

    if uploaded:
        image_bytes = uploaded.getvalue()
        media_type = uploaded.type or "image/jpeg"
        st.image(image_bytes, use_container_width=True)

        lat, lng = None, None
        gps = get_location_from_exif(image_bytes)
        if gps:
            lat, lng = gps
            st.success(f"📍 {lat:.5f}, {lng:.5f}")
        else:
            st.info("No GPS in photo — enter a location.")
            address = st.text_input(
                "Address or intersection",
                placeholder="199 Chambers St, New York, NY",
                key=f"{key_prefix}_address",
            )
            if address:
                coords = geocode_address(address)
                if coords:
                    lat, lng = coords
                    st.success(f"📍 {lat:.5f}, {lng:.5f}")
                else:
                    st.error("Couldn't find that address. Try adding the borough or zip.")

        if lat is not None and st.button(
            "Classify & add to map",
            type="primary",
            use_container_width=True,
            key=f"{key_prefix}_classify",
        ):
            with st.spinner("Classifying with Claude Vision..."):
                result = classify_image(image_bytes, media_type=media_type)
            if result["category"] == "other":
                st.warning(
                    "🚫 This doesn't look like trash or a reportable NYC civic issue. "
                    "Nothing was saved or added to the map."
                )
                if result.get("reasoning"):
                    st.caption(result["reasoning"])
            else:
                guide = get_guide(result["category"])
                save_pin(
                    lat=lat,
                    lng=lng,
                    category=result["category"],
                    display_name=guide["display_name"],
                    image_bytes=image_bytes,
                    reasoning=result.get("reasoning", ""),
                    notable_details=result.get("notable_details", ""),
                    confidence=result.get("confidence", ""),
                )
                st.session_state.last_result = (result, guide)
                st.rerun()

    if st.session_state.last_result:
        result, guide = st.session_state.last_result
        st.divider()
        st.subheader(f"How to report: {guide['display_name']}")
        st.markdown(f"**Detected:** `{result['category']}` · {result['confidence']}")
        if result.get("reasoning"):
            st.caption(result["reasoning"])
        st.markdown(f"**Agency:** {guide['agency']}")
        st.markdown(f"**Channel:** {guide['channel']}")
        st.markdown(f"**Select:** _{guide['service_type']}_")
        st.markdown(f"**What to do:** {guide['instructions']}")
        if result.get("notable_details"):
            st.info(f"Include: {result['notable_details']}")
        if guide.get("link"):
            st.link_button("Open reporting page", guide["link"], use_container_width=True)


def _render_desktop_layout() -> None:
    left, right = st.columns([7, 3], gap="large")
    with right:
        _render_upload_panel(key_prefix="d")
    with left:
        st_folium(_build_folium_map(), width=None, height=1200, returned_objects=[], key="d_map")


def _render_mobile_panel() -> None:
    """Dense mobile upload/result panel. Uses horizontal columns aggressively — never stacks
    content vertically when 2-col side-by-side fits. Never scrolls; the parent is capped at 50vh.
    """
    pin_count = len(load_pins())
    has_result = st.session_state.last_result is not None

    # Header row — title + pin count inline (leaves right half empty when no result)
    hdr = st.columns([3, 2])
    with hdr[0]:
        st.markdown("<div class='tai-m-title'>TrashAI</div>", unsafe_allow_html=True)
    with hdr[1]:
        st.markdown(
            f"<div class='tai-m-pins'>📍 {pin_count} pinned</div>",
            unsafe_allow_html=True,
        )

    if is_stub_mode() and not has_result:
        st.caption("⚙️ Stub mode — add API key for real classification")

    uploaded = st.file_uploader(
        "Upload",
        type=["jpg", "jpeg", "png"],
        key="m_file",
        label_visibility="collapsed",
    )

    # Pristine-state marker: no file and no result. CSS :has() uses this to shrink the
    # panel so the map fills more of the screen on the very initial page load.
    if uploaded is None and not has_result:
        st.markdown(
            "<div data-tai-pristine='1' style='display:none'></div>",
            unsafe_allow_html=True,
        )

    if uploaded:
        image_bytes = uploaded.getvalue()
        media_type = uploaded.type or "image/jpeg"

        lat, lng = None, None
        gps = get_location_from_exif(image_bytes)

        img_col, info_col = st.columns([1, 3])
        with img_col:
            st.image(image_bytes, width=64)
        with info_col:
            if gps:
                lat, lng = gps
                st.success(f"📍 {lat:.4f}, {lng:.4f}")
            else:
                address = st.text_input(
                    "Address",
                    placeholder="199 Chambers St, NY",
                    key="m_addr",
                    label_visibility="collapsed",
                )
                if address:
                    coords = geocode_address(address)
                    if coords:
                        lat, lng = coords
                        st.caption(f"📍 {lat:.4f}, {lng:.4f}")
                    else:
                        st.caption("⚠️ Not found. Add borough or zip.")

        if lat is not None and st.button(
            "Classify & add to map",
            type="primary",
            use_container_width=True,
            key="m_classify",
        ):
            with st.spinner("Classifying..."):
                result = classify_image(image_bytes, media_type=media_type)
            if result["category"] == "other":
                st.warning("🚫 Not a reportable NYC issue. Not saved.")
                if result.get("reasoning"):
                    st.caption(result["reasoning"])
            else:
                guide = get_guide(result["category"])
                save_pin(
                    lat=lat,
                    lng=lng,
                    category=result["category"],
                    display_name=guide["display_name"],
                    image_bytes=image_bytes,
                    reasoning=result.get("reasoning", ""),
                    notable_details=result.get("notable_details", ""),
                    confidence=result.get("confidence", ""),
                )
                st.session_state.last_result = (result, guide)
                st.rerun()

    if has_result:
        result, guide = st.session_state.last_result
        # Result title + Open-report button on same row (right half uses the "dead space")
        rhdr = st.columns([3, 2])
        with rhdr[0]:
            st.markdown(
                f"<div class='tai-m-restitle'>{html.escape(guide['display_name'])}</div>",
                unsafe_allow_html=True,
            )
        with rhdr[1]:
            if guide.get("link"):
                st.link_button("Open report", guide["link"], use_container_width=True)

        # Dense info row: agency/channel on left, service type on right
        meta = st.columns([3, 2])
        with meta[0]:
            st.markdown(
                f"<div class='tai-m-meta'><b>{html.escape(guide['agency'])}</b> · {html.escape(guide['channel'])}</div>",
                unsafe_allow_html=True,
            )
        with meta[1]:
            st.markdown(
                f"<div class='tai-m-meta tai-m-svc'><i>{html.escape(guide['service_type'])}</i></div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div class='tai-m-instr'>{html.escape(guide['instructions'])}</div>",
            unsafe_allow_html=True,
        )
        if result.get("notable_details"):
            st.markdown(
                f"<div class='tai-m-notes'>ℹ️ {html.escape(result['notable_details'])}</div>",
                unsafe_allow_html=True,
            )


def _render_mobile_layout() -> None:
    with st.container(key="mobile-panel"):
        _render_mobile_panel()
    st_folium(_build_folium_map(), width=None, height=600, returned_objects=[], key="m_map")


st.set_page_config(page_title="TrashAI", page_icon="📍", layout="wide")

if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.markdown(
    """
    <style>
    /* --- Global resets shared by both layouts --- */
    [data-testid='stFileUploaderDropzoneInstructions'] small,
    [data-testid='stFileUploaderDropzoneInstructions'] span:last-child,
    [data-testid='stFileDropzoneInstructions'] small,
    [data-testid='stFileUploaderDropzone'] small {display:none !important;}

    html, body {overflow: hidden !important; height: 100vh !important; margin: 0 !important; padding: 0 !important;}
    [data-testid='stApp'], [data-testid='stAppViewContainer'],
    [data-testid='stMain'], .stMain, section.main {
      overflow: hidden !important; height: 100vh !important; max-height: 100vh !important;
    }
    header[data-testid='stHeader'], [data-testid='stToolbar'], footer {display: none !important;}
    [data-testid='stMainBlockContainer'], section.main > div.block-container,
    .block-container, div.block-container {
      padding: 0 !important; margin: 0 !important;
      max-width: 100% !important; width: 100% !important;
      height: 100vh !important; max-height: 100vh !important;
      overflow: hidden !important;
    }

    /* --- Only one root renders per viewport --- */
    @media (min-width: 641px) { .st-key-mobile-root {display: none !important;} }
    @media (max-width: 640px) { .st-key-desktop-root {display: none !important;} }
    .st-key-desktop-root, .st-key-mobile-root {height: 100vh !important; width: 100% !important;}

    /* =========================================================
       DESKTOP LAYOUT (scoped to .st-key-desktop-root)
       ========================================================= */
    @media (min-width: 641px) {
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] {
        gap: 0 !important;
        height: 100vh !important; min-height: 100vh !important;
        margin: 0 !important;
      }
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn'] {
        height: 100vh !important; max-height: 100vh !important;
      }
      /* Left column (map): no padding, fill */
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child,
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child > div[data-testid='stVerticalBlock'],
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stElementContainer'],
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stVerticalBlockBorderWrapper'] {
        padding: 0 !important; gap: 0 !important; height: 100vh !important;
      }
      /* Map iframe fills full viewport */
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child iframe,
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stIFrame'],
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stCustomComponentV1'],
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [class*='Component'],
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [title^='streamlit_folium'] {
        height: 100vh !important; width: 100% !important; display: block !important;
        border: 0 !important; min-height: 100vh !important;
      }
      /* Right column: scroll internally */
      .st-key-desktop-root div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child {
        overflow-y: auto !important;
        padding: 1.5rem 1.75rem !important;
      }
    }

    /* =========================================================
       MOBILE LAYOUT (scoped to .st-key-mobile-root)
       Dynamic split: panel grows from min 30vh up to max 50vh as content is added.
       Map always fills remaining space (always >= 50vh, up to 70vh when panel is minimal).
       Panel uses horizontal columns aggressively; Streamlit's default mobile-stacking is overridden.
       ========================================================= */
    @media (max-width: 640px) {
      .st-key-mobile-root {
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important; max-height: 100vh !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
      }
      /* Inner stVerticalBlock = flex column holding (panel, map). */
      .st-key-mobile-root > div[data-testid='stVerticalBlockBorderWrapper'] {
        height: 100vh !important; max-height: 100vh !important;
        width: 100% !important;
      }
      .st-key-mobile-root > div[data-testid='stVerticalBlockBorderWrapper'] > div[data-testid='stVerticalBlock'] {
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important; max-height: 100vh !important;
        width: 100% !important;
        gap: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
      }

      /* --- Panel: non-pristine = 50vh (fixed), pristine = 12vh (fixed).
         Fixed heights so the map's explicit vh heights never overlap or leave gaps. --- */
      .st-key-mobile-panel {
        flex: 0 0 50vh !important;
        height: 50vh !important; max-height: 50vh !important;
        width: 100% !important;
        padding: 0.5rem !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
      }
      .st-key-mobile-panel:has([data-tai-pristine]) {
        flex: 0 0 12vh !important;
        height: 12vh !important; max-height: 12vh !important;
      }
      .st-key-mobile-panel > div[data-testid='stVerticalBlock'] {
        gap: 0.35rem !important;
        height: 100% !important;
      }

      /* --- Map: explicit viewport heights, no cascade dependency. --- */
      /* Default (non-pristine): map = 50vh */
      .st-key-mobile-root [data-testid='stElementContainer']:has(iframe[title^='streamlit_folium']),
      .st-key-mobile-root [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) {
        flex: 0 0 50vh !important;
        height: 50vh !important; min-height: 50vh !important; max-height: 50vh !important;
        width: 100% !important;
        display: block !important;
        overflow: hidden !important;
        margin: 0 !important; padding: 0 !important;
      }
      .st-key-mobile-root [data-testid='stElementContainer']:has(iframe[title^='streamlit_folium']) iframe,
      .st-key-mobile-root [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) iframe,
      .st-key-mobile-root [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) [data-testid='stCustomComponentV1'],
      .st-key-mobile-root [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) [data-testid='stIFrame'] {
        height: 50vh !important; min-height: 50vh !important; max-height: 50vh !important;
        width: 100% !important;
        display: block !important;
        border: 0 !important;
      }

      /* Pristine: map = 88vh (takes whatever's left after the 12vh panel) */
      .st-key-mobile-root:has([data-tai-pristine]) [data-testid='stElementContainer']:has(iframe[title^='streamlit_folium']),
      .st-key-mobile-root:has([data-tai-pristine]) [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) {
        flex: 0 0 88vh !important;
        height: 88vh !important; min-height: 88vh !important; max-height: 88vh !important;
      }
      .st-key-mobile-root:has([data-tai-pristine]) [data-testid='stElementContainer']:has(iframe[title^='streamlit_folium']) iframe,
      .st-key-mobile-root:has([data-tai-pristine]) [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) iframe,
      .st-key-mobile-root:has([data-tai-pristine]) [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) [data-testid='stCustomComponentV1'],
      .st-key-mobile-root:has([data-tai-pristine]) [data-testid='stElementContainer']:has([data-testid='stCustomComponentV1']) [data-testid='stIFrame'] {
        height: 88vh !important; min-height: 88vh !important; max-height: 88vh !important;
      }

      /* :has() fallback (older browsers) — skip pristine shrink, keep 50/50 */
      @supports not selector(:has(*)) {
        .st-key-mobile-panel {height: 50vh !important; max-height: 50vh !important;}
        .st-key-mobile-root iframe[title^='streamlit_folium'],
        .st-key-mobile-root [data-testid='stCustomComponentV1'],
        .st-key-mobile-root [data-testid='stIFrame'] {
          height: 50vh !important; min-height: 50vh !important;
          width: 100% !important; display: block !important; border: 0 !important;
        }
      }

      /* --- CRITICAL: force st.columns to stay horizontal on mobile.
         Streamlit's default CSS stacks columns at narrow widths; we override it here so our 2-col
         dense layouts (title|pin, thumb|address, result-title|link-button, agency|service-type)
         actually render side-by-side. --- */
      .st-key-mobile-panel div[data-testid='stHorizontalBlock'] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
        margin: 0 !important;
        width: 100% !important;
      }
      .st-key-mobile-panel div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn'] {
        min-width: 0 !important;
        padding: 0 !important;
      }

      /* Element container margins zeroed */
      .st-key-mobile-panel [data-testid='stElementContainer'] {margin: 0 !important;}

      /* Custom header classes */
      .st-key-mobile-root .tai-m-title {
        font-size: 1.2rem; font-weight: 700; line-height: 1.15; margin: 0; padding: 0;
      }
      .st-key-mobile-root .tai-m-pins {
        font-size: 0.78rem; line-height: 1.15; text-align: right; opacity: 0.85;
        padding-top: 0.35rem;
      }
      .st-key-mobile-root .tai-m-restitle {
        font-size: 1rem; font-weight: 700; line-height: 1.2; margin: 0; padding-top: 0.3rem;
      }
      .st-key-mobile-root .tai-m-meta {
        font-size: 0.75rem; line-height: 1.25; margin: 0;
      }
      .st-key-mobile-root .tai-m-svc {text-align: right;}
      .st-key-mobile-root .tai-m-instr {
        font-size: 0.75rem; line-height: 1.3; margin: 0.15rem 0 0 0; opacity: 0.92;
      }
      .st-key-mobile-root .tai-m-notes {
        font-size: 0.7rem; line-height: 1.25; margin: 0.15rem 0 0 0; opacity: 0.75;
      }

      /* Heading/markdown resets */
      .st-key-mobile-root h1, .st-key-mobile-root h2, .st-key-mobile-root h3 {
        display: block !important; position: static !important;
      }
      .st-key-mobile-root [data-testid='stHeading'],
      .st-key-mobile-root [data-testid='stMarkdownContainer'] {
        margin: 0 !important; padding: 0 !important; display: block !important; position: static !important;
      }
      .st-key-mobile-root [data-testid='stCaptionContainer'],
      .st-key-mobile-root .stCaption,
      .st-key-mobile-root small {
        margin: 0 !important; padding: 0 !important; line-height: 1.2 !important; font-size: 0.72rem !important;
      }
      .st-key-mobile-root [data-testid='stAlert'] {
        padding: 0.25rem 0.45rem !important; margin: 0 !important; font-size: 0.75rem !important;
      }

      /* File uploader: compact; hide the dropzone instructions once a file is uploaded to save ~60px */
      .st-key-mobile-root [data-testid='stFileUploader'] {
        margin: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow: hidden !important;
      }
      .st-key-mobile-root [data-testid='stFileUploaderDropzone'] {
        padding: 0.5rem 0.75rem !important;
        min-height: 0 !important;
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
      }
      /* Inner section/div: center within parent; let widths flow naturally so nothing overflows */
      .st-key-mobile-root [data-testid='stFileUploaderDropzone'] > section,
      .st-key-mobile-root [data-testid='stFileUploaderDropzone'] > div {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        align-items: center !important;
        max-width: 100% !important;
        min-width: 0 !important;
        flex: 0 1 auto !important;
        gap: 0.5rem !important;
      }
      .st-key-mobile-root [data-testid='stFileUploaderDropzoneInstructions'] {
        padding: 0 !important;
        margin: 0 !important;
        flex: 0 1 auto !important;
        min-width: 0 !important;
        max-width: 100% !important;
      }
      /* Browse files button — keep inside the dropzone bounds */
      .st-key-mobile-root [data-testid='stFileUploaderDropzone'] button {
        flex: 0 0 auto !important;
        max-width: 100% !important;
        min-width: 0 !important;
        white-space: nowrap !important;
      }
      .st-key-mobile-root [data-testid='stFileUploaderFile'] {
        padding: 0.15rem 0.3rem !important; font-size: 0.72rem !important;
      }
      .st-key-mobile-root [data-testid='stFileUploader']:has([data-testid='stFileUploaderFile']) [data-testid='stFileUploaderDropzone'] {
        display: none !important;
      }

      /* Form controls — flat, tight */
      .st-key-mobile-root [data-testid='stTextInput'] input {
        padding: 0.2rem 0.5rem !important; font-size: 0.78rem !important; height: 1.8rem !important; min-height: 0 !important;
      }
      .st-key-mobile-root [data-testid='stButton'] button {
        padding: 0.2rem 0.5rem !important; font-size: 0.8rem !important; min-height: 0 !important; height: 1.9rem !important;
      }
      .st-key-mobile-root [data-testid='stLinkButton'] a {
        padding: 0.2rem 0.4rem !important; font-size: 0.75rem !important; min-height: 0 !important; height: 1.8rem !important;
        display: inline-flex !important; align-items: center !important; justify-content: center !important;
      }

      /* Thumbnail (64px) inside the upload row */
      .st-key-mobile-root [data-testid='stImage'],
      .st-key-mobile-root [data-testid='stImage'] > div,
      .st-key-mobile-root [data-testid='stImage'] figure {
        width: 64px !important; max-width: 64px !important; min-width: 0 !important;
        margin: 0 !important; padding: 0 !important; display: block !important;
      }
      .st-key-mobile-root [data-testid='stImage'] img {
        width: 64px !important; height: 64px !important;
        max-width: 64px !important; max-height: 64px !important;
        object-fit: cover !important; border-radius: 6px !important; display: block !important;
      }

      /* Safety: no element in the panel may overflow horizontally */
      .st-key-mobile-panel [data-testid='stElementContainer'] {
        max-width: 100% !important; box-sizing: border-box !important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="desktop-root"):
    _render_desktop_layout()

with st.container(key="mobile-root"):
    _render_mobile_layout()
