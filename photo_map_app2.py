
import streamlit as st
import gpxpy
import pandas as pd
import folium
from streamlit_folium import st_folium
import exifread
from PIL import Image
from io import BytesIO
import base64

st.set_page_config(layout="wide")
st.title("写真付き登山ルートビューワー")

uploaded_gpx = st.file_uploader("GPXファイルを選択", type="gpx")
uploaded_photos = st.file_uploader("写真を選択（複数可）", type=["jpg", "jpeg","JPG","JPEG"], accept_multiple_files=True)

def get_gps_from_exif(img_file):
    tags = exifread.process_file(img_file, details=False)
    try:
        lat_ref = tags["GPS GPSLatitudeRef"].values
        lon_ref = tags["GPS GPSLongitudeRef"].values
        lat = tags["GPS GPSLatitude"].values
        lon = tags["GPS GPSLongitude"].values

        def convert(value):
            return float(value.num) / float(value.den)

        lat_deg = convert(lat[0])
        lat_min = convert(lat[1])
        lat_sec = convert(lat[2])
        lon_deg = convert(lon[0])
        lon_min = convert(lon[1])
        lon_sec = convert(lon[2])

        latitude = lat_deg + lat_min / 60 + lat_sec / 3600
        longitude = lon_deg + lon_min / 60 + lon_sec / 3600

        if lat_ref != "N":
            latitude = -latitude
        if lon_ref != "E":
            longitude = -longitude

        return latitude, longitude
    except:
        return None, None

if uploaded_gpx:
    gpx = gpxpy.parse(uploaded_gpx)
    coords = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coords.append((point.latitude, point.longitude))

    center = coords[len(coords) // 2]
    m = folium.Map(location=center, zoom_start=14)
    folium.PolyLine(coords, color="blue", weight=3).add_to(m)
    folium.Marker(coords[0], popup="スタート", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(coords[-1], popup="ゴール", icon=folium.Icon(color='red')).add_to(m)

    # 写真付きマーカー追加
    for photo in uploaded_photos:
        img_data = photo.read()
        img_io = BytesIO(img_data)
        img_io.seek(0)
        lat, lon = get_gps_from_exif(img_io)

        if lat and lon:
            encoded = base64.b64encode(img_data).decode()
            html = f'<img src="data:image/jpeg;base64,{encoded}" width="200">'
            popup = folium.Popup(html, max_width=250)
            folium.Marker([lat, lon], popup=popup, icon=folium.Icon(color='orange', icon='camera')).add_to(m)

    st.subheader("登山ルートと写真マップ")
    st_folium(m, width=800, height=500)
