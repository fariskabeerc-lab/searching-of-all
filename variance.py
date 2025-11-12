import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
from pyzbar import pyzbar
import cv2

# --- Hide Streamlit Branding ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Page Config ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")
st.title("🏪 Outlet-wise Sales Insights Dashboard")

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Cache Data ---
@st.cache_data
def load_data():
    df = pd.read_excel("column wise.Xlsx")
    df.columns = df.columns.str.strip()
    return df

# --- Barcode Scanner Processor ---
class BarcodeScanner(VideoProcessorBase):
    def __init__(self):
        self.detected_code = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = pyzbar.decode(img)
        for barcode in barcodes:
            self.detected_code = barcode.data.decode("utf-8")
            # Draw rectangle on barcode
            x, y, w, h = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, self.detected_code, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return img

if password == "123123":
    st.success("✅ Access Granted")
    df = load_data()

    # Identify outlet columns
    outlet_cols = [c for c in df.columns if c not in ["Item Code", "Items"]]

    # --- Sidebar Outlet Selector ---
    selected_outlet = st.sidebar.selectbox(
        "🏬 Select Outlet:",
        ["All Outlets"] + sorted(outlet_cols)
    )

    # --- Live Barcode Scanner ---
    st.subheader("📷 Scan Barcode (or search manually)")
    barcode_processor = BarcodeScanner()
    webrtc_ctx = webrtc_streamer(
        key="barcode-scanner",
        video_processor_factory=lambda: barcode_processor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True
    )

    # --- Manual search as fallback ---
    search_term = st.text_input(
        "🔍 Or type Item Name / Barcode manually:"
    ).strip()

    # Determine what to search: scanned barcode has priority
    if barcode_processor.detected_code:
        search_term = barcode_processor.detected_code

    if search_term:
        filtered_df = df[
            df["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if not filtered_df.empty:
            item_name = filtered_df.iloc[0]["Items"]
            st.subheader(f"📦 Results for: **{item_name}**")

            # --- Melt for chart and table ---
            outlet_sales = filtered_df.melt(
                id_vars=["Item Code", "Items"],
                value_vars=outlet_cols,
                var_name="Outlet",
                value_name="Qty Sold"
            )
            outlet_sales["Qty Sold"] = pd.to_numeric(outlet_sales["Qty Sold"], errors="coerce").fillna(0)

            # Apply outlet filter
            if selected_outlet != "All Outlets":
                outlet_sales = outlet_sales[outlet_sales["Outlet"] == selected_outlet]

            outlet_sales = outlet_sales[outlet_sales["Qty Sold"] > 0]

            # Avg Monthly Sale (+1)
            outlet_sales["Avg Monthly Sale"] = (outlet_sales["Qty Sold"] / 10 + 1).astype(int)

            # Info box
            avg_sale = outlet_sales["Avg Monthly Sale"].mean()
            st.info(f"**Avg Monthly Sale per Item:** {int(avg_sale)} units")

            # Horizontal Bar Chart
            fig = px.bar(
                outlet_sales.sort_values("Qty Sold", ascending=True),
                x="Qty Sold",
                y="Outlet",
                orientation="h",
                text="Qty Sold",
                color="Qty Sold",
                color_continuous_scale="Blues",
                hover_data={"Item Code": True, "Items": True, "Avg Monthly Sale": True}
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(title_x=0.3, yaxis_title="Outlet", xaxis_title="Quantity Sold")
            st.plotly_chart(fig, use_container_width=True)

            # Detailed Table
            st.markdown("### 📋 Outlet-wise Detailed Sales (with Avg Monthly Sale)")
            st.dataframe(
                outlet_sales[["Item Code", "Items", "Outlet", "Qty Sold", "Avg Monthly Sale"]]
                .sort_values("Qty Sold", ascending=False),
                use_container_width=True
            )

        else:
            st.warning("🔎 No matching items found. Try another search term.")

elif password:
    st.error("❌ Incorrect Password.")
else:
    st.info("🔒 Please enter the password to access the dashboard.")
