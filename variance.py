import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Setup ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")
st.title("🏪 Outlet-wise Sales Insights Dashboard")

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Load Data Once and Cache ---
@st.cache_data
def load_data():
    file_path = "sales with outlet.xlsx"   # 👈 change path if needed
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    return df

if password == "123123":
    st.success("✅ Access Granted")

    # Load data from cache
    df = load_data()

    required_cols = {"Outlet", "Item Code", "Items", "Qty Sold"}
    if not required_cols.issubset(df.columns):
        st.error(f"⚠️ Missing columns. Your file must have: {', '.join(required_cols)}")

    else:
        # --- Search Box ---
        search_term = st.text_input("🔍 Search for an Item (by name or code):").strip()

        if search_term:
            # --- Filter the Data Fast ---
            mask = df["Items"].astype(str).str.contains(search_term, case=False, na=False) | \
                   df["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = df[mask]

            if not filtered_df.empty:
                st.subheader(f"📦 Results for: **{search_term}**")

                # --- Aggregate outlet-wise sales ---
                outlet_sales = (
                    filtered_df.groupby("Outlet", as_index=False)["Qty Sold"]
                    .sum()
                    .sort_values("Qty Sold", ascending=False)
                )

                # --- Insights ---
                total_qty = outlet_sales["Qty Sold"].sum()
                top_outlet = outlet_sales.iloc[0]
                low_outlet = outlet_sales.iloc[-1]

                st.markdown("### 📊 Insights")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Quantity Sold", f"{int(total_qty)} Units")
                col2.metric("🏆 Top Outlet", f"{top_outlet['Outlet']}", f"{int(top_outlet['Qty Sold'])} Units")
                col3.metric("📉 Lowest Outlet", f"{low_outlet['Outlet']}", f"{int(low_outlet['Qty Sold'])} Units")

                # --- Horizontal Bar Chart ---
                fig = px.bar(
                    outlet_sales,
                    y="Outlet",
                    x="Qty Sold",
                    orientation="h",
                    text="Qty Sold",
                    color="Qty Sold",
                    color_continuous_scale="Blues",
                    title=f"Outlet-wise Sales for '{search_term}'"
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(yaxis_title="Outlet", xaxis_title="Quantity Sold", title_x=0.3)
                st.plotly_chart(fig, use_container_width=True)

                # --- Detailed Table ---
                st.markdown("### 📋 Detailed Item-wise Data")
                item_table = (
                    filtered_df.groupby(["Outlet", "Items"], as_index=False)["Qty Sold"]
                    .sum()
                    .sort_values(["Outlet", "Qty Sold"], ascending=[True, False])
                )
                st.dataframe(item_table, use_container_width=True)

            else:
                st.warning("🔎 No matching items found. Try another search term.")

elif password:
    st.error("❌ Incorrect Password.")
else:
    st.info("🔒 Please enter the password to access the dashboard.")
