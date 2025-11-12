import streamlit as st
import pandas as pd
import plotly.express as px

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
    df = pd.read_excel("column wise.Xlsx")  # 👈 your file
    df.columns = df.columns.str.strip()
    return df

if password == "123123":
    st.success("✅ Access Granted")
    df = load_data()

    # Identify outlet columns
    outlet_cols = [c for c in df.columns if c not in ["Item Code", "Items"]]

    # --- Sidebar: Outlet Selector ---
    selected_outlet = st.sidebar.selectbox(
        "🏬 Select Outlet:",
        ["All Outlets"] + sorted(outlet_cols)
    )

    # --- Main Page: Search Box ---
    search_term = st.text_input("🔍 Search by Item Name or Barcode:").strip()

    if search_term:
        # --- Filter by Name or Barcode ---
        filtered_df = df[
            df["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if not filtered_df.empty:
            item_name = filtered_df.iloc[0]["Items"]
            st.subheader(f"📦 Results for: **{item_name}**")

            # --- Melt data for plotting and table ---
            outlet_sales = filtered_df.melt(
                id_vars=["Item Code", "Items"],
                value_vars=outlet_cols,
                var_name="Outlet",
                value_name="Qty Sold"
            )
            outlet_sales["Qty Sold"] = pd.to_numeric(outlet_sales["Qty Sold"], errors="coerce").fillna(0)

            # --- Apply outlet filter ---
            if selected_outlet != "All Outlets":
                outlet_sales = outlet_sales[outlet_sales["Outlet"] == selected_outlet]

            outlet_sales = outlet_sales[outlet_sales["Qty Sold"] > 0]

            # --- Average Monthly Sales (+1) ---
            outlet_sales["Avg Monthly Sale"] = (outlet_sales["Qty Sold"] / 10 + 1).astype(int)

            # --- Overall Avg Monthly Sale for Info Box ---
            avg_sale = outlet_sales["Avg Monthly Sale"].mean()
            st.info(f"**Avg Monthly Sale per Item:** {int(avg_sale)} units")

            # --- Horizontal Bar Chart ---
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

            # --- Detailed Table ---
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
