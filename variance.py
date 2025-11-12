import streamlit as st
import pandas as pd
import plotly.express as px

# --- Hide Fork & Toolbar ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Page Config ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")
st.title("🏪 Outlet-wise Sales Insights Dashboard")

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Load & Cache Data ---
@st.cache_data
def load_data():
    df = pd.read_excel("column wise.Xlsx")
    df.columns = df.columns.str.strip()
    return df

if password == "123123":
    st.success("✅ Access Granted")

    # Load data
    df = load_data()

    # Identify outlet columns
    outlet_cols = [col for col in df.columns if col not in ["Item Code", "Items"]]

    # --- Search Box ---
    search_term = st.text_input("🔍 Search for an Item (by name or code):").strip()

    if search_term:
        # --- Fast Filtering ---
        filtered = df[
            df["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if not filtered.empty:
            # Get the unique barcode(s)
            item_codes = filtered["Item Code"].unique()
            item_codes_text = ", ".join(map(str, item_codes))

            st.subheader(f"📦 Results for: **{search_term}** (Barcode: {item_codes_text})")

            # --- Aggregate Outlet Sales (sum all matching items) ---
            summed = filtered[outlet_cols].sum(numeric_only=True)
            outlet_sales = summed.reset_index()
            outlet_sales.columns = ["Outlet", "Qty Sold"]
            outlet_sales["Qty Sold"] = pd.to_numeric(outlet_sales["Qty Sold"], errors="coerce").fillna(0)
            outlet_sales["Avg Monthly Sales"] = outlet_sales["Qty Sold"] / 10  # Jan–Oct = 10 months
            outlet_sales["Item Code(s)"] = item_codes_text  # attach barcodes for hover/table

            # --- Insights ---
            total_qty = outlet_sales["Qty Sold"].sum()
            top_outlet = outlet_sales.loc[outlet_sales["Qty Sold"].idxmax()]
            low_outlet = outlet_sales.loc[outlet_sales["Qty Sold"].idxmin()]

            st.markdown("### 📊 Insights")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Sold (Jan–Oct)", f"{int(total_qty)} Units")
            col2.metric("Avg Monthly Sales (All Outlets)", f"{int(total_qty/10)} Units")
            col3.metric("🏆 Top Outlet", f"{top_outlet['Outlet']}", f"{int(top_outlet['Qty Sold'])} Units")
            col4.metric("📉 Lowest Outlet", f"{low_outlet['Outlet']}", f"{int(low_outlet['Qty Sold'])} Units")

            # --- Horizontal Bar Chart ---
            fig = px.bar(
                outlet_sales.sort_values("Qty Sold", ascending=True),
                y="Outlet",
                x="Qty Sold",
                orientation="h",
                text="Qty Sold",
                color="Qty Sold",
                color_continuous_scale="Blues",
                title=f"Outlet-wise Total Sales for '{search_term}' (Jan–Oct)",
                hover_data={
                    "Outlet": True,
                    "Qty Sold": True,
                    "Avg Monthly Sales": True,
                    "Item Code(s)": True
                }
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis_title="Outlet",
                xaxis_title="Quantity Sold (Jan–Oct)",
                title_x=0.3,
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Detailed Table ---
            st.markdown("### 📋 Outlet-wise Sales & Monthly Average with Barcode")
            st.dataframe(
                outlet_sales[["Item Code(s)", "Outlet", "Qty Sold", "Avg Monthly Sales"]]
                .sort_values("Qty Sold", ascending=False)
                .reset_index(drop=True),
                use_container_width=True
            )

        else:
            st.warning("🔎 No matching items found. Try another search term.")
elif password:
    st.error("❌ Incorrect Password.")
else:
    st.info("🔒 Please enter the password to access the dashboard.")
