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


st.set_page_config(page_title="TrashAI", page_icon="📍", layout="wide")

if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.markdown(
    """
    <style>
    [data-testid='stFileUploaderDropzoneInstructions'] small,
    [data-testid='stFileUploaderDropzoneInstructions'] span:last-child,
    [data-testid='stFileDropzoneInstructions'] small,
    [data-testid='stFileUploaderDropzone'] small {display:none !important;}

    /* Desktop: full-viewport map on left, scroll panel on right, no page scroll */
    @media (min-width: 641px) {
      html, body {overflow: hidden !important; height: 100vh !important;}
      [data-testid='stApp'], [data-testid='stAppViewContainer'],
      [data-testid='stMain'], .stMain, section.main {
        overflow: hidden !important; height: 100vh !important; max-height: 100vh !important;
      }
      header[data-testid='stHeader'] {display: none !important;}
      [data-testid='stToolbar'] {display: none !important;}
      footer {display: none !important;}

      [data-testid='stMainBlockContainer'], section.main > div.block-container,
      .block-container, div.block-container {
        padding: 0 !important; margin: 0 !important;
        max-width: 100% !important; width: 100% !important;
        height: 100vh !important; max-height: 100vh !important;
        overflow: hidden !important;
      }

      /* Columns row fills viewport */
      div[data-testid='stHorizontalBlock'] {
        gap: 0 !important;
        height: 100vh !important; min-height: 100vh !important;
        margin: 0 !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn'] {
        height: 100vh !important; max-height: 100vh !important;
      }
      /* Left column (map): no padding, fill */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child,
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child > div[data-testid='stVerticalBlock'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stElementContainer'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stVerticalBlockBorderWrapper'] {
        padding: 0 !important; gap: 0 !important; height: 100vh !important;
      }
      /* Component iframe wrapper + iframe fill full viewport */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child iframe,
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stIFrame'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stCustomComponentV1'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [class*='Component'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [title^='streamlit_folium'] {
        height: 100vh !important; width: 100% !important; display: block !important;
        border: 0 !important; min-height: 100vh !important;
      }
      /* Right column: scroll internally */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child {
        overflow-y: auto !important;
        padding: 1.5rem 1.75rem !important;
      }
    }
    /* Mobile: no scroll anywhere, upload on top (compact), map filling remaining viewport */
    @media (max-width: 640px) {
      html, body {overflow: hidden !important; height: 100vh !important; margin: 0 !important; padding: 0 !important;}
      [data-testid='stApp'], [data-testid='stAppViewContainer'],
      [data-testid='stMain'], .stMain, section.main {
        overflow: hidden !important; height: 100vh !important; max-height: 100vh !important;
      }
      header[data-testid='stHeader'], [data-testid='stToolbar'], footer {display: none !important;}

      [data-testid='stMainBlockContainer'], section.main > div.block-container,
      .block-container, div.block-container {
        padding: 0.5rem !important; margin: 0 !important;
        max-width: 100% !important; width: 100% !important;
        height: 100vh !important; max-height: 100vh !important;
        overflow: hidden !important;
      }

      /* Compact typography and killed vertical gaps in the upload panel */
      h1 {font-size: 1.35rem !important; line-height: 1.2 !important; margin: 0 0 0.4rem 0 !important; padding: 0 !important;}
      [data-testid='stHeading'], [data-testid='stMarkdownContainer'] {margin: 0 !important; padding: 0 !important; display: block !important; position: static !important;}
      h1, h2, h3 {display: block !important; position: static !important;}
      [data-testid='stCaptionContainer'], .stCaption, small {
        margin: 0 !important; padding: 0 !important; line-height: 1.3 !important; font-size: 0.8rem !important; display: block !important;
      }
      [data-testid='stAlert'] {padding: 0.35rem 0.5rem !important; margin: 0.2rem 0 !important;}
      [data-testid='stFileUploader'] label {font-size: 0.8rem !important; margin-bottom: 0.15rem !important;}
      [data-testid='stFileUploaderDropzone'] {padding: 0.4rem 0.6rem !important; min-height: 0 !important;}
      /* Kill default 1rem gaps in vertical blocks on mobile */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child div[data-testid='stVerticalBlock'] {
        gap: 0.25rem !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child [data-testid='stElementContainer'] {
        margin: 0 !important;
      }

      /* Horizontal block becomes a column: upload (last child) stacks on top, map (first child) below */
      div[data-testid='stHorizontalBlock'] {
        display: flex !important;
        flex-direction: column-reverse !important;
        height: calc(100vh - 1rem) !important;
        max-height: calc(100vh - 1rem) !important;
        gap: 0.35rem !important;
        margin: 0 !important;
      }
      /* Upload column: natural height, no scroll unless very tall */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child {
        flex: 0 0 auto !important;
        width: 100% !important;
        padding: 0 !important;
        max-height: 55vh !important;
        overflow-y: auto !important;
      }
      /* Map column: force explicit viewport-based height (flex propagation unreliable through streamlit wrappers) */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child {
        flex: 1 1 auto !important;
        width: 100% !important;
        padding: 0 !important;
        overflow: hidden !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child > div[data-testid='stVerticalBlock'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stElementContainer'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stVerticalBlockBorderWrapper'] {
        padding: 0 !important; gap: 0 !important; margin: 0 !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child iframe,
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stIFrame'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stCustomComponentV1'] {
        height: calc(100vh - 255px) !important;
        min-height: 280px !important;
        width: 100% !important;
        display: block !important;
        border: 0 !important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([7, 3], gap="large")

with right:
    st.title("TrashAI")
    st.caption("Snap a photo of anything needing civic action in NYC. We'll tell you exactly where and how to report it.")
    if is_stub_mode():
        st.warning("⚙️ Stub mode: Claude Vision is disabled. Add your API key to `.streamlit/secrets.toml` to enable real classification.")
    pin_count = len(load_pins())
    st.caption(f"📍 {pin_count} pinned on the map")
    uploaded = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])
    st.markdown("<p style='font-size:0.75rem;font-style:italic;font-weight:600;color:#888;text-align:center;margin-top:2px'>AI can make mistakes.<br>Always verify the category and instructions before filing a report.</p>", unsafe_allow_html=True)

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
            address = st.text_input("Address or intersection", placeholder="199 Chambers St, New York, NY")
            if address:
                coords = geocode_address(address)
                if coords:
                    lat, lng = coords
                    st.success(f"📍 {lat:.5f}, {lng:.5f}")
                else:
                    st.error("Couldn't find that address. Try adding the borough or zip.")

        if lat is not None and st.button("Classify & add to map", type="primary", use_container_width=True):
            with st.spinner("Classifying with Claude Vision..."):
                result = classify_image(image_bytes, media_type=media_type)
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

with left:
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
    st_folium(m, width=None, height=1200, returned_objects=[])
