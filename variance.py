import streamlit as st
import pandas as pd
import plotly.express as px
from functools import reduce


# --- Page Config ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")
st.title("🏪 Sales QTY Check -JAN to NOV")

# --- UI FIXES (DO NOT AFFECT LOGIC) ---
st.markdown("""
<style>
/* Hide sidebar collapse button */
button[kind="header"] {
    display: none;
}

/* Keep sidebar always visible */
section[data-testid="stSidebar"] {
    min-width: 280px;
    max-width: 280px;
}

/* Hide Streamlit menu, footer, deploy */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Configuration (Your file names) ---
DATA_FILES = [
    "Month wise full outlet sales(1).xlsx",
    "Month wise full outlet sales.Xlsx",
]

# --- Master Month List for Chronological Ordering ---
MASTER_MONTH_ORDER = [
    'Jan-2025', 'Feb-2025', 'Mar-2025', 'Apr-2025', 'May-2025', 'Jun-2025',
    'Jul-2025', 'Aug-2025', 'Sep-2025', 'Oct-2025', 'Nov-2025', 'Dec-2025'
]

# --- Cache Data Loading and Merging ---
@st.cache_data
def load_all_data(files_list):
    data_frames = []

    for file_path in files_list:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        data_frames.append(df)

    master_df = pd.concat(data_frames, ignore_index=True)

    if 'Company Name' in master_df.columns:
        master_df = master_df.rename(columns={'Company Name': 'Outlet'})
    else:
        st.error("The required column 'Company Name' was not found.")
        return None

    month_cols = [c for c in master_df.columns if c in MASTER_MONTH_ORDER]

    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)

    return master_df, month_cols


# --- Main Logic Start ---
if password == "123123":
    st.success("✅ Access Granted")

    loaded_data = load_all_data(DATA_FILES)
    if loaded_data is None:
        st.stop()

    df_combined, month_cols = loaded_data

    # --- Sidebar: Outlet Selector ---
    all_outlets = sorted(df_combined['Outlet'].unique().tolist())
    selected_outlet = st.sidebar.selectbox(
        "🏬 Select Outlet:",
        ["All Outlets"] + all_outlets
    )

    # --- Main Page: Search Box ---
    search_term = st.text_input("🔍 Search by Item Name or Barcode:").strip()
    search_terms = search_term.split()

    if search_term:

        # Apply Outlet Filter
        if selected_outlet != "All Outlets":
            df_filtered = df_combined[df_combined["Outlet"] == selected_outlet].copy()
        else:
            df_filtered = df_combined.copy()

        # 🔁 MULTIPLE ITEM LOOP
        for term in search_terms:

            filtered_df_item = df_filtered[
                df_filtered["Items"].astype(str).str.contains(term, case=False, na=False)
                | df_filtered["Item Code"].astype(str).str.contains(term, case=False, na=False)
            ]

            if filtered_df_item.empty:
                st.warning(f"🔎 No matching items found for **{term}**")
                continue

            matching_items = filtered_df_item[['Item Code', 'Items']].drop_duplicates()

            if len(matching_items) > 1:
                item_options = matching_items['Items'].tolist()
                selected_item_name = st.selectbox(
                    f"Select specific item for search '{term}':",
                    item_options,
                    key=term
                )
                final_item_df = filtered_df_item[
                    filtered_df_item['Items'] == selected_item_name
                ]
            else:
                final_item_df = filtered_df_item
                selected_item_name = final_item_df.iloc[0]["Items"]

            st.divider()
            st.subheader(f"📦 Monthly Sales Breakdown for: **{selected_item_name}**")

            # --- Aggregate and Melt data ---
            monthly_sales_summary = final_item_df.groupby(['Outlet'])[month_cols].sum().reset_index()

            monthly_sales_melted = monthly_sales_summary.melt(
                id_vars="Outlet",
                value_vars=month_cols,
                var_name="Month",
                value_name="Qty Sold"
            )

            monthly_sales_melted_plot = monthly_sales_melted[
                monthly_sales_melted["Qty Sold"] > 0
            ]

            if monthly_sales_melted_plot.empty:
                st.warning("No sales data found.")
                continue

            # --- GRAND TOTAL ---
            grand_total_qty = monthly_sales_melted_plot['Qty Sold'].sum()
            st.metric(
                label=f"🏆 GRAND TOTAL QUANTITY SOLD ({selected_item_name})",
                value=f"{grand_total_qty:,.0f} units"
            )

            # --- Chart ---
            present_month_order = [
                m for m in MASTER_MONTH_ORDER
                if m in monthly_sales_melted_plot['Month'].unique()
            ]

            fig = px.bar(
                monthly_sales_melted_plot,
                x="Qty Sold",
                y="Outlet",
                color="Month",
                orientation="h",
                title="Total Sales Quantity by Outlet, Segmented by Month",
                color_discrete_sequence=px.colors.sequential.Blues_r,
                category_orders={"Month": present_month_order}
            )

            fig.update_traces(marker_line_width=1, marker_line_color='black')
            fig.update_layout(
                xaxis_title="Quantity Sold",
                yaxis_title="Outlet",
                yaxis={'categoryorder': 'total ascending'},
                legend_title_text='Month',
                margin=dict(r=100)
            )

            outlet_totals = monthly_sales_melted_plot.groupby(
                'Outlet')['Qty Sold'].sum().reset_index()
            outlet_totals.columns = ['Outlet', 'Total Sales (Qty)']

            for _, row in outlet_totals.iterrows():
                fig.add_annotation(
                    x=row['Total Sales (Qty)'],
                    y=row['Outlet'],
                    text=f"{row['Total Sales (Qty)']:.0f}",
                    showarrow=False,
                    xshift=10,
                    font=dict(size=12, weight='bold')
                )

            st.plotly_chart(fig, use_container_width=True)

            # --- Tables ---
            st.markdown("### 🏷️ Total Sales Quantity by Outlet")
            st.dataframe(
                outlet_totals.sort_values('Total Sales (Qty)', ascending=False),
                use_container_width=True
            )

            st.markdown("### 📋 Monthly Sales Breakdown")
            display_cols = ['Outlet'] + month_cols
            st.dataframe(
                monthly_sales_summary[display_cols].sort_values("Outlet"),
                use_container_width=True
            )

    else:
        st.info("👈 Use the sidebar and search box (multiple barcodes supported)")

elif password:
    st.error("❌ Incorrect Password.")
