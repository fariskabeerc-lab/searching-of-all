import streamlit as st
import pandas as pd
import plotly.express as px
from functools import reduce

# --- Page Config ---
# We use st.session_state to track if the sidebar should be open or closed
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.set_page_config(
    page_title="Outlet Sales Insights", 
    layout="wide", 
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- Hide "Fork" and Streamlit Branding ---
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* This removes the padding at the top so it looks cleaner */
    .block-container {padding-top: 2rem;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- Sidebar Toggle Function ---
def toggle_sidebar():
    if st.session_state.sidebar_state == "expanded":
        st.session_state.sidebar_state = "collapsed"
    else:
        st.session_state.sidebar_state = "expanded"

# --- Main UI ---
st.title("🏪 Sales QTY Check - JAN to NOV")

# Button to open/close the filter bar
if st.button("📁 Toggle Filter Bar"):
    toggle_sidebar()
    st.rerun()

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Configuration ---
DATA_FILES = [
    "Month wise full outlet sales(1).xlsx",
    "Month wise full outlet sales.Xlsx",
]

MASTER_MONTH_ORDER = [
    'Jan-2025', 'Feb-2025', 'Mar-2025', 'Apr-2025', 'May-2025', 'Jun-2025',
    'Jul-2025', 'Aug-2025', 'Sep-2025', 'Oct-2025', 'Nov-2025', 'Dec-2025'
]

@st.cache_data
def load_all_data(files_list):
    data_frames = []
    for file_path in files_list:
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            data_frames.append(df)
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            return None

    if not data_frames: return None
    master_df = pd.concat(data_frames, ignore_index=True)
    
    if 'Company Name' in master_df.columns:
        master_df = master_df.rename(columns={'Company Name': 'Outlet'})
    else:
        st.error("The required column 'Company Name' was not found.")
        return None
    
    all_cols = master_df.columns.tolist()
    month_cols = [c for c in all_cols if c in MASTER_MONTH_ORDER] 

    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)
        
    return master_df, month_cols

# --- Main Logic ---
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
    search_input = st.text_input("🔍 Search by Item Name or Barcode (Separate multiple with space):").strip()

    if search_input:
        # Split search input by spaces to handle multiple barcodes/names
        search_terms = [term.strip() for term in search_input.split(" ") if term.strip()]
        
        # Apply Outlet Filter FIRST
        if selected_outlet != "All Outlets":
            df_filtered_base = df_combined[df_combined["Outlet"] == selected_outlet].copy()
        else:
            df_filtered_base = df_combined.copy()

        # Loop through each search term and display details "one by one"
        for term in search_terms:
            st.divider() # Visual separator for multiple items
            
            # Apply Item Search Filter for this specific term
            filtered_df_item = df_filtered_base[
                df_filtered_base["Items"].astype(str).str.contains(term, case=False, na=False)
                | df_filtered_base["Item Code"].astype(str).str.contains(term, case=False, na=False)
            ]

            if not filtered_df_item.empty:
                matching_items = filtered_df_item[['Item Code', 'Items']].drop_duplicates()
                
                # If one search term matches multiple actual items (like "Milk")
                if len(matching_items) > 1:
                    item_options = matching_items['Items'].tolist()
                    selected_item_name = st.selectbox(f"Multiple items found for '{term}'. Select one:", item_options, key=f"select_{term}")
                    final_item_df = filtered_df_item[filtered_df_item['Items'] == selected_item_name]
                else:
                    final_item_df = filtered_df_item
                    selected_item_name = final_item_df.iloc[0]["Items"]

                st.subheader(f"📦 Results for: **{selected_item_name}**")
                
                # --- Aggregate and Melt ---
                monthly_sales_summary = final_item_df.groupby(['Outlet'])[month_cols].sum().reset_index()
                monthly_sales_melted = monthly_sales_summary.melt(
                    id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty Sold"
                )
                monthly_sales_melted_plot = monthly_sales_melted[monthly_sales_melted["Qty Sold"] > 0]
                
                if not monthly_sales_melted_plot.empty:
                    grand_total_qty = monthly_sales_melted_plot['Qty Sold'].sum()
                    st.metric(label=f"🏆 GRAND TOTAL ({selected_item_name})", value=f"{grand_total_qty:,.0f} units")
                    
                    # --- Chart ---
                    present_month_order = [m for m in MASTER_MONTH_ORDER if m in monthly_sales_melted_plot['Month'].unique()]
                    fig = px.bar(
                        monthly_sales_melted_plot, x="Qty Sold", y="Outlet", color="Month", 
                        orientation="h", title=f"Sales for {selected_item_name}",
                        color_discrete_sequence=px.colors.sequential.Blues_r,
                        category_orders={"Month": present_month_order} 
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(r=100))
                    
                    # Labels
                    outlet_totals = monthly_sales_melted_plot.groupby('Outlet')['Qty Sold'].sum().reset_index()
                    for _, row in outlet_totals.iterrows():
                        fig.add_annotation(x=row['Qty Sold'], y=row['Outlet'], text=f"{row['Qty Sold']:.0f}",
                                           showarrow=False, xanchor='left', xshift=10, font=dict(weight='bold'))

                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{term}_{selected_item_name}")
                    
                    # Tables
                    with st.expander(f"View Data Tables for {selected_item_name}"):
                        st.dataframe(outlet_totals.sort_values('Qty Sold', ascending=False), use_container_width=True)
                        st.dataframe(monthly_sales_summary[['Outlet'] + month_cols], use_container_width=True)
                else:
                    st.warning(f"No sales data found for '{term}'.")
            else:
                st.warning(f"🔎 No matching items found for: **{term}**")
                
    elif password == "123123" and not search_input:
        st.info("👈 Open the filter bar or enter barcodes above to begin.")

elif password:
    st.error("❌ Incorrect Password.")
elif not password:
    st.info("🔒 Please enter the password to access the dashboard.")
