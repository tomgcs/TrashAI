import base64
from io import BytesIO

import folium
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from classify import classify_image
from location import geocode_address, get_location_from_exif
from routing import get_guide

NYC_CENTER = [40.7128, -74.0060]


def _thumbnail(image_bytes: bytes, max_size: int = 400) -> bytes:
    img = Image.open(BytesIO(image_bytes))
    img.thumbnail((max_size, max_size))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


st.set_page_config(page_title="TrashAI", page_icon="📍", layout="wide")

if "pins" not in st.session_state:
    st.session_state.pins = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

st.title("TrashAI")
st.caption("Snap a photo of anything needing civic action in NYC. We'll tell you exactly where and how to report it.")

uploaded = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])

if uploaded:
    image_bytes = uploaded.getvalue()
    media_type = uploaded.type or "image/jpeg"

    col_img, col_side = st.columns([1, 1])
    with col_img:
        st.image(image_bytes, use_container_width=True)

    lat, lng = None, None
    with col_side:
        gps = get_location_from_exif(image_bytes)
        if gps:
            lat, lng = gps
            st.success(f"📍 Location detected from photo: {lat:.5f}, {lng:.5f}")
        else:
            st.info("No GPS data in this photo — tell us where you saw it.")
            address = st.text_input("Address or nearest intersection", placeholder="199 Chambers St, New York, NY")
            if address:
                coords = geocode_address(address)
                if coords:
                    lat, lng = coords
                    st.success(f"📍 Geocoded: {lat:.5f}, {lng:.5f}")
                else:
                    st.error("Couldn't find that address. Try adding the borough or zip.")

        if lat is not None and st.button("Classify & add to map", type="primary"):
            with st.spinner("Classifying with Claude Vision..."):
                result = classify_image(image_bytes, media_type=media_type)
            guide = get_guide(result["category"])
            st.session_state.pins.append(
                {
                    "lat": lat,
                    "lng": lng,
                    "category": result["category"],
                    "display_name": guide["display_name"],
                    "image_bytes": image_bytes,
                }
            )
            st.session_state.last_result = (result, guide)

if st.session_state.last_result:
    result, guide = st.session_state.last_result
    st.divider()
    st.subheader(f"How to report: {guide['display_name']}")
    meta_col, action_col = st.columns([2, 1])
    with meta_col:
        st.markdown(f"**Detected as:** `{result['category']}` — confidence: {result['confidence']}")
        if result.get("reasoning"):
            st.caption(result["reasoning"])
        st.markdown(f"**Agency:** {guide['agency']}")
        st.markdown(f"**Channel:** {guide['channel']}")
        st.markdown(f"**Select:** _{guide['service_type']}_")
        st.markdown(f"**What to do:** {guide['instructions']}")
        if result.get("notable_details"):
            st.info(f"Include in your report: {result['notable_details']}")
    with action_col:
        if guide.get("link"):
            st.link_button("Open reporting page", guide["link"], use_container_width=True)

st.divider()
st.subheader(f"Map ({len(st.session_state.pins)} pinned)")
m = folium.Map(location=NYC_CENTER, zoom_start=11, tiles="cartodbpositron")
for pin in st.session_state.pins:
    thumb_b64 = base64.b64encode(_thumbnail(pin["image_bytes"])).decode("utf-8")
    popup_html = (
        f"<b>{pin['display_name']}</b><br>"
        f"<img src='data:image/jpeg;base64,{thumb_b64}' width='200'>"
    )
    folium.Marker(
        [pin["lat"], pin["lng"]],
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=pin["display_name"],
    ).add_to(m)
st_folium(m, width=None, height=500, returned_objects=[])
