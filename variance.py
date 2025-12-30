import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# --- Page Config ---
# =========================
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")

st.title("🏪 Sales QTY Check - JAN to NOV")

st.set_page_config(layout="wide")

st.markdown("""
<style>
/* Force hide Streamlit header toolbar */
header [data-testid="stToolbarActions"] {
    visibility: hidden !important;
}

/* Force hide 3-dot menu */
header [data-testid="stMainMenu"] {
    visibility: hidden !important;
}
</style>
""", unsafe_allow_html=True)



# =========================
# --- Password Protection ---
# =========================
password = st.text_input("🔑 Enter Password:", type="password")

# =========================
# --- Configuration ---
# =========================
DATA_FILES = [
    "Month wise full outlet sales(1).xlsx",
    "Month wise full outlet sales.Xlsx"
]

MASTER_MONTH_ORDER = [
    'Jan-2025', 'Feb-2025', 'Mar-2025', 'Apr-2025', 'May-2025', 'Jun-2025',
    'Jul-2025', 'Aug-2025', 'Sep-2025', 'Oct-2025', 'Nov-2025', 'Dec-2025'
]

# =========================
# --- Load and Merge Data ---
# =========================
@st.cache_data
def load_all_data(files_list):
    data_frames = []

    for file_path in files_list:
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            data_frames.append(df)
        except FileNotFoundError:
            st.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            return None

    if not data_frames:
        return None

    master_df = pd.concat(data_frames, ignore_index=True)

    if 'Company Name' in master_df.columns:
        master_df = master_df.rename(columns={'Company Name': 'Outlet'})
    else:
        st.error("Column 'Company Name' not found in the dataset.")
        return None

    month_cols = [c for c in master_df.columns if c in MASTER_MONTH_ORDER]
    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)

    return master_df, month_cols

# =========================
# --- Main App Logic ---
# =========================
if password == "123123":
    st.success("✅ Access Granted")

    data_load = load_all_data(DATA_FILES)
    if data_load is None:
        st.stop()
    
    df, month_cols = data_load

    # --- Sidebar: Outlet Selection ---
    outlets = sorted(df['Outlet'].unique())
    selected_outlet = st.sidebar.selectbox("🏬 Select Outlet:", ["All Outlets"] + outlets)

    # --- Main Search Box ---
    search_input = st.text_input("🔍 Search Item Name or Item Code (separate multiple with space):").strip()

    if search_input:
        # Split input by spaces to create a list of exact terms
        search_terms = [term.strip() for term in search_input.split() if term.strip()]

        # Apply outlet filter first
        df_filtered = df[df["Outlet"] == selected_outlet] if selected_outlet != "All Outlets" else df.copy()

        # --- Exact Match Filter ---
        # .isin() ensures it only matches the full string, not a partial piece
        df_filtered = df_filtered[
            df_filtered["Items"].astype(str).isin(search_terms) | 
            df_filtered["Item Code"].astype(str).isin(search_terms)
        ]

        if not df_filtered.empty:
            unique_items = df_filtered['Items'].unique()
            for item in unique_items:
                st.divider()
                st.subheader(f"📦 Sales Breakdown: **{item}**")

                item_df = df_filtered[df_filtered['Items'] == item]
                monthly_summary = item_df.groupby('Outlet')[month_cols].sum().reset_index()
                
                monthly_melted = monthly_summary.melt(
                    id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty Sold"
                )
                monthly_melted_plot = monthly_melted[monthly_melted["Qty Sold"] > 0]

                if not monthly_melted_plot.empty:
                    # --- Grand Total ---
                    grand_total = monthly_melted_plot['Qty Sold'].sum()
                    st.metric("🏆 GRAND TOTAL", f"{grand_total:,.0f} units")

                    # --- Stacked Bar Chart ---
                    month_order = [m for m in MASTER_MONTH_ORDER if m in monthly_melted_plot['Month'].unique()]
                    fig = px.bar(
                        monthly_melted_plot,
                        x="Qty Sold",
                        y="Outlet",
                        color="Month",
                        orientation="h",
                        title=f"{item} - Outlet Sales by Month",
                        category_orders={"Month": month_order},
                        color_discrete_sequence=px.colors.sequential.Blues_r
                    )
                    fig.update_traces(marker_line_width=1, marker_line_color='black')

                    # Add total per outlet label
                    totals = monthly_melted_plot.groupby('Outlet')['Qty Sold'].sum().reset_index()
                    for _, row in totals.iterrows():
                        fig.add_annotation(
                            x=row['Qty Sold'], y=row['Outlet'],
                            text=f"{row['Qty Sold']:.0f}",
                            showarrow=False, xanchor='left', xshift=10,
                            font=dict(size=12, color='black')
                        )

                    fig.update_layout(
                        xaxis_title="Quantity Sold",
                        yaxis_title="Outlet",
                        yaxis={'categoryorder':'total ascending'},
                        margin=dict(r=120)
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # --- Data Tables ---
                    with st.expander(f"See Tables for {item}"):
                        st.markdown("### Outlet-wise Total Sales")
                        st.dataframe(totals.sort_values('Qty Sold', ascending=False), use_container_width=True)

                        st.markdown("### Monthly Sales Breakdown")
                        st.dataframe(monthly_summary.sort_values('Outlet'), use_container_width=True)
                else:
                    st.warning(f"No sales data found for **{item}**.")
        else:
            st.warning("🔎 No exact matching items found. Please check your spelling or code.")
    else:
        st.info("👈 Enter an item name or barcode above to view sales breakdown. Use the sidebar to filter by outlet.")

elif password:
    st.error("❌ Incorrect Password.")
    st.error("❌ Incorrect Password.")
