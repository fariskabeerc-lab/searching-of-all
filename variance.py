import streamlit as st
import pandas as pd
import plotly.express as px
from functools import reduce

# --- Page Config ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")

# --- CUSTOM CSS TO HIDE THE RIGHT-SIDE TOOLBAR ONLY ---
st.markdown("""
    <style>
    /* Hides the header (Deploy button, hamburger menu, etc.) */
    header {visibility: hidden;}
    
    /* Optional: Reduces top padding so the app starts higher up */
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏪 Sales QTY Check -JAN to NOV")

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
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            data_frames.append(df)
        except FileNotFoundError:
            st.error(f"File not found: {file_path}.")
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
    selected_outlet = st.sidebar.selectbox("🏬 Select Outlet:", ["All Outlets"] + all_outlets)

    # --- Search Box (Handles multiple barcodes/names) ---
    search_input = st.text_input("🔍 Search by Item Name or Barcode (separate multiple items with a space):").strip()

    if search_input:
        # Split by spaces to handle multiple barcodes
        search_terms = [term.strip() for term in search_input.split() if term.strip()]
        search_pattern = "|".join(search_terms)
        
        # Filter logic
        if selected_outlet != "All Outlets":
            df_filtered = df_combined[df_combined["Outlet"] == selected_outlet].copy()
        else:
            df_filtered = df_combined.copy()
            
        filtered_df_item = df_filtered[
            df_filtered["Items"].astype(str).str.contains(search_pattern, case=False, na=False)
            | df_filtered["Item Code"].astype(str).str.contains(search_pattern, case=False, na=False)
        ]

        if not filtered_df_item.empty:
            unique_items = filtered_df_item['Items'].unique()

            # --- Process each found item ---
            for selected_item_name in unique_items:
                st.divider()
                final_item_df = filtered_df_item[filtered_df_item['Items'] == selected_item_name]
                st.subheader(f"📦 Monthly Sales Breakdown for: **{selected_item_name}**")
                
                # Aggregate Data
                monthly_sales_summary = final_item_df.groupby(['Outlet'])[month_cols].sum().reset_index()
                monthly_sales_melted = monthly_sales_summary.melt(
                    id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty Sold"
                )
                monthly_sales_melted_plot = monthly_sales_melted[monthly_sales_melted["Qty Sold"] > 0]
                
                if not monthly_sales_melted_plot.empty:
                    # Metric
                    grand_total_qty = monthly_sales_melted_plot['Qty Sold'].sum()
                    st.metric(label="🏆 GRAND TOTAL QUANTITY SOLD", value=f"{grand_total_qty:,.0f} units")
                    
                    # --- Chart with Total Labels ---
                    st.markdown(f"### 📊 {selected_item_name}: Outlet Sales Total")
                    
                    present_month_order = [m for m in MASTER_MONTH_ORDER if m in monthly_sales_melted_plot['Month'].unique()]
                    
                    fig = px.bar(
                        monthly_sales_melted_plot,
                        x="Qty Sold",
                        y="Outlet",
                        color="Month", 
                        orientation="h",
                        title=f"Total Sales Quantity by Outlet: {selected_item_name}",
                        hover_data={"Qty Sold": True, "Month": True, "Outlet": True},
                        color_discrete_sequence=px.colors.sequential.Blues_r,
                        category_orders={"Month": present_month_order} 
                    )
                    
                    fig.update_traces(marker_line_width=1, marker_line_color='black')
                    
                    # Grouping for annotations (The Totals)
                    outlet_totals = monthly_sales_melted_plot.groupby('Outlet')['Qty Sold'].sum().reset_index()

                    # Add labels at the end of bars
                    for _, row in outlet_totals.iterrows():
                        fig.add_annotation(
                            x=row['Qty Sold'],
                            y=row['Outlet'],
                            text=f"<b>{row['Qty Sold']:.0f}</b>", # Bolder total value
                            showarrow=False,
                            xanchor='left',
                            xshift=10, 
                            font=dict(size=13, color='black')
                        )

                    fig.update_layout(
                        xaxis_title="Quantity Sold", 
                        yaxis_title="Outlet",
                        yaxis={'categoryorder':'total ascending'},
                        legend_title_text='Month',
                        margin=dict(r=120) # More space on the right for labels
                    )

                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{selected_item_name}") 
                    
                    # Tables
                    with st.expander(f"View Data Tables for {selected_item_name}"):
                        st.dataframe(outlet_totals.sort_values('Qty Sold', ascending=False), use_container_width=True)
                        st.dataframe(monthly_sales_summary, use_container_width=True)

                else:
                    st.warning(f"No sales data found for **{selected_item_name}**.")
        else:
            st.warning("🔎 No matching items found.")
            
    elif not password:
        st.info("🔒 Please enter the password.")
    elif password == "123123" and not search_input:
        st.info("👈 Enter item names or barcodes above. Separate multiple items with a space.")

elif password:
    st.error("❌ Incorrect Password.")
