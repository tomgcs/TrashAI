import base64
import html
from io import BytesIO

import folium
import streamlit as st
from PIL import Image, ImageOps
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

from classify import classify_image, is_stub_mode
from groups import join_group, load_groups, save_group
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
    img = ImageOps.exif_transpose(img)
    img.thumbnail((max_size, max_size))
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


st.set_page_config(page_title="TrashAI", page_icon="📍", layout="wide")

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "groups_mode" not in st.session_state:
    st.session_state.groups_mode = False
if "display_name" not in st.session_state:
    st.session_state.display_name = None
if "create_group_open" not in st.session_state:
    st.session_state.create_group_open = False

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
      /* Right column: scroll internally, tighter gaps */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child {
        overflow-y: auto !important;
        padding: 1.5rem 1.75rem !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child > div[data-testid='stVerticalBlock'] {
        gap: 0.5rem !important;
      }
    }
    /* Mobile: stack panel on top, map below — breakpoint raised to 900px for safety */
    @media (max-width: 900px) {
      html, body {overflow: hidden !important; height: 100vh !important; margin: 0 !important; padding: 0 !important; overflow-x: hidden !important;}
      [data-testid='stApp'], [data-testid='stAppViewContainer'],
      [data-testid='stMain'], .stMain, section.main {
        overflow: hidden !important; height: 100vh !important; max-height: 100vh !important;
      }
      header[data-testid='stHeader'], [data-testid='stToolbar'], footer {display: none !important;}
      [data-testid='stMainBlockContainer'], section.main > div.block-container,
      .block-container, div.block-container {
        padding: 0 !important; margin: 0 !important;
        max-width: 100vw !important; width: 100% !important;
        height: 100vh !important; overflow: hidden !important;
      }

      /* Stack columns vertically: panel (last) on top, map (first) below */
      div[data-testid='stHorizontalBlock'] {
        display: flex !important;
        flex-direction: column-reverse !important;
        height: 100vh !important;
        width: 100% !important;
        max-width: 100vw !important;
        gap: 0 !important;
        margin: 0 !important;
        overflow-x: hidden !important;
      }

      /* Force both columns full width when stacked */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn'] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100vw !important;
        flex: none !important;
      }

      /* Panel: fixed height, scrollable internally, compact padding */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child {
        height: 45vh !important;
        max-height: 45vh !important;
        overflow-y: auto !important;
        padding: 0.75rem 1rem !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:last-child div[data-testid='stVerticalBlock'] {
        gap: 0.35rem !important;
      }

      /* Map: fills remaining 55vh */
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child {
        height: 55vh !important;
        padding: 0 !important;
        overflow: hidden !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child > div[data-testid='stVerticalBlock'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stElementContainer'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stVerticalBlockBorderWrapper'] {
        padding: 0 !important; gap: 0 !important; margin: 0 !important; height: 100% !important;
      }
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child iframe,
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stIFrame'],
      div[data-testid='stHorizontalBlock'] > div[data-testid='stColumn']:first-child [data-testid='stCustomComponentV1'] {
        height: 55vh !important;
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
        st.caption("⚙️ Stub mode — add API key to `.streamlit/secrets.toml` to enable Claude Vision.")
    pin_count = len(load_pins())
    st.caption(f"📍 {pin_count} pinned on the map")

    # Mode toggle
    mode = st.radio("", ["📤  Upload", "👤  Groups"], horizontal=True,
                    label_visibility="collapsed",
                    index=1 if st.session_state.groups_mode else 0)
    st.session_state.groups_mode = (mode == "👤  Groups")

    # ── Upload mode ──────────────────────────────────────────────────────────
    if not st.session_state.groups_mode:
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
                st.info("No GPS in photo — share your current location or enter an address.")

                if st.button("📍 Use my current location", use_container_width=True):
                    st.session_state.geo_requested = True

                if st.session_state.get("geo_requested"):
                    loc = get_geolocation()
                    if loc and loc.get("coords"):
                        lat = loc["coords"]["latitude"]
                        lng = loc["coords"]["longitude"]
                        st.success(f"📍 {lat:.5f}, {lng:.5f}")
                    else:
                        st.caption("Allow location access in your browser when prompted…")

                if lat is None:
                    address = st.text_input("Or address / intersection", placeholder="199 Chambers St, New York, NY")
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

    # ── Groups mode ───────────────────────────────────────────────────────────
    else:
        if st.session_state.display_name is None:
            st.markdown("**What's your name?**")
            st.caption("Only used to identify you in groups. Never stored beyond this session.")
            name = st.text_input("Display name", placeholder="e.g. Alex", label_visibility="collapsed")
            if st.button("Continue", type="primary", use_container_width=True):
                if name.strip():
                    st.session_state.display_name = name.strip()
                    st.rerun()
                else:
                    st.error("Please enter a name.")
        else:
            st.caption(f"Signed in as **{st.session_state.display_name}**")

            with st.expander("➕  Create a group", expanded=st.session_state.create_group_open):
                st.session_state.create_group_open = True
                g_title = st.text_input("Group name", placeholder="Prospect Park Cleanup")
                g_neighborhood = st.text_input("Neighborhood", placeholder="Park Slope, Brooklyn")
                g_location = st.text_input("Meetup location", placeholder="Main entrance, 9th St & Prospect Park W")
                g_time = st.text_input("When", placeholder="Saturday Apr 26 at 10am")
                if st.button("Create group", type="primary", use_container_width=True):
                    if g_title.strip() and g_neighborhood.strip() and g_location.strip() and g_time.strip():
                        save_group(g_title.strip(), g_neighborhood.strip(), g_location.strip(), g_time.strip(), st.session_state.display_name)
                        st.session_state.create_group_open = False
                        st.rerun()
                    else:
                        st.error("Fill in all four fields.")

            groups = load_groups()
            if not groups:
                st.info("No groups yet — create one above.")
            else:
                for g in groups:
                    members = g.get("members", [])
                    member_count = len(members)
                    is_member = st.session_state.display_name in members
                    label = f"{'✓ ' if is_member else ''}**{g['title']}** · 👥 {member_count}"
                    with st.expander(label):
                        st.caption(f"📍 {g['neighborhood']}  ·  🕐 {g['meetup_time']}")
                        st.caption(f"📌 {g.get('meetup_location', 'TBD')}")
                        st.caption(f"Started by {g['creator']}")
                        st.markdown("**Members:**")
                        for m in members:
                            st.markdown(f"- {m}")
                        if not is_member:
                            if st.button("Join", key=f"join_{g['id']}", use_container_width=True):
                                join_group(g["id"], st.session_state.display_name)
                                st.rerun()
                        else:
                            st.success("✓ You're in this group")

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
