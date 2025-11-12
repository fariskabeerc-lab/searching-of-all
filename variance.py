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
    df = pd.read_excel("sales with outlet.xlsx")
    df.columns = df.columns.str.strip()
    return df

# --- Proceed only if password is correct ---
if password == "123123":
    st.success("✅ Access Granted")

    df = load_data()

    # Identify outlet columns dynamically (everything except Item Code and Items)
    outlet_cols = [col for col in df.columns if col not in ["Item Code", "Items"]]

    # --- Search Input ---
    search_term = st.text_input("🔍 Search for an Item (by name or code):").strip()

    if search_term:
        # Fast filter
        filtered = df[
            df["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if not filtered.empty:
            st.subheader(f"📦 Results for: **{search_term}**")

            # Take the first matching item row
            item_row = filtered.iloc[0]

            # Create a melted dataframe for easier plotting
            outlet_sales = (
                item_row[outlet_cols]
                .reset_index()
                .rename(columns={"index": "Outlet", 0: "Qty Sold"})
            )
            outlet_sales["Qty Sold"] = outlet_sales["Qty Sold"].astype(float)
            outlet_sales["Avg Monthly Sales"] = outlet_sales["Qty Sold"] / 10  # 10 months average

            # --- Insights ---
            top_outlet = outlet_sales.loc[outlet_sales["Qty Sold"].idxmax()]
            low_outlet = outlet_sales.loc[outlet_sales["Qty Sold"].idxmin()]
            total_qty = outlet_sales["Qty Sold"].sum()

            st.markdown("### 📊 Insights")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Sold (Jan–Oct)", f"{int(total_qty)} Units")
            col2.metric("Avg Monthly Sales (All Outlets)", f"{int(total_qty/10)} Units")
            col3.metric("🏆 Top Outlet", f"{top_outlet['Outlet']}", f"{int(top_outlet['Qty Sold'])} Units")
            col4.metric("📉 Lowest Outlet", f"{low_outlet['Outlet']}", f"{int(low_outlet['Qty Sold'])} Units")

            # --- Horizontal Bar Chart (Outlet vs Qty Sold) ---
            fig = px.bar(
                outlet_sales.sort_values("Qty Sold", ascending=True),
                y="Outlet",
                x="Qty Sold",
                orientation="h",
                text="Qty Sold",
                color="Qty Sold",
                color_continuous_scale="Blues",
                title=f"Outlet-wise Total Sales for '{search_term}' (Jan–Oct)"
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(title_x=0.3, yaxis_title="Outlet", xaxis_title="Qty Sold (Jan–Oct)")
            st.plotly_chart(fig, use_container_width=True)

            # --- Detailed Table ---
            st.markdown("### 📋 Outlet-wise Sales & Monthly Average")
            st.dataframe(
                outlet_sales.sort_values("Qty Sold", ascending=False).reset_index(drop=True),
                use_container_width=True
            )

        else:
            st.warning("🔎 No matching items found. Try another search term.")
elif password:
    st.error("❌ Incorrect Password.")
else:
    st.info("🔒 Please enter the password to access the dashboard.")
