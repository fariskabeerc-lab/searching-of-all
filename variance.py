import streamlit as st
import pandas as pd
import plotly.express as px
from functools import reduce

# --- CSS to hide Streamlit elements ---
hide_css = """
<style>
/* Try to hide specific buttons by title (works in many cases) */
button[title="Fork"] {display:none !important;}
button[title="Share"] {display:none !important;}

/* Hide header and footer as fallback */
header {visibility: hidden !important;}
footer {visibility: hidden !important;}

/* Additional generic fallbacks */
div[role="toolbar"] {display:none !important;}
</style>
"""
st.markdown(hide_css, unsafe_allow_html=True)


# --- Page Config ---
st.set_page_config(page_title="Monthly Sales Insights", layout="wide")
st.title("🗓️ Sales QTY Check - Monthly Trend") # Title updated to reflect monthly view

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Configuration (Your file names) ---
DATA_FILES = [
    "Month wise full outlet sales(1).xlsx",
    "Month wise full outlet sales.Xlsx",
]

# --- Cache Data Loading and Merging ---
@st.cache_data
def load_all_data(files_list):
    data_frames = []
    
    # List of all expected monthly columns
    MONTHLY_COLUMNS = [f"{m}-{y}" for y in ["2025"] for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]]
    
    # 1. Load each dataset and concatenate
    for file_path in files_list:
        try:
            df = pd.read_excel(file_path)
            # Standardize column names
            df.columns = df.columns.str.strip()
            data_frames.append(df)
        except FileNotFoundError:
            st.error(f"File not found: {file_path}. Please check your file path.")
            return None
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
            return None

    if not data_frames:
        return None

    # 2. Concatenate all dataframes into a single master dataframe
    master_df = pd.concat(data_frames, ignore_index=True)
    
    # 3. Clean and prepare data
    if 'Company Name' in master_df.columns:
        # Rename 'Company Name' to 'Outlet' for consistency
        master_df = master_df.rename(columns={'Company Name': 'Outlet'})
    else:
        st.error("The required column 'Company Name' was not found in the datasets.")
        return None
    
    # Identify the actual monthly columns present
    all_cols = master_df.columns.tolist()
    month_cols = [c for c in all_cols if c in MONTHLY_COLUMNS]

    # Convert monthly columns to numeric
    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)
        
    return master_df, month_cols

# --- Main Logic Start ---

if password == "123123":
    st.success("✅ Access Granted")
    
    # Load and merge data
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

    if search_term:
        
        # 1. Apply Outlet Filter FIRST
        if selected_outlet != "All Outlets":
            df_filtered = df_combined[df_combined["Outlet"] == selected_outlet].copy()
        else:
            df_filtered = df_combined.copy()
            
        # 2. Apply Item Search Filter
        filtered_df_item = df_filtered[
            df_filtered["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df_filtered["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if not filtered_df_item.empty:
            
            # --- Handle Multiple Item Matches (for display clarity) ---
            matching_items = filtered_df_item[['Item Code', 'Items']].drop_duplicates()
            
            if len(matching_items) > 1:
                item_options = matching_items['Items'].tolist()
                selected_item_name = st.selectbox("Select specific item:", item_options)
                final_item_df = filtered_df_item[filtered_df_item['Items'] == selected_item_name]
            else:
                final_item_df = filtered_df_item
                selected_item_name = final_item_df.iloc[0]["Items"]

            st.subheader(f"📦 Monthly Trend for: **{selected_item_name}**")
            
            # --- Aggregate and Melt data for Time Series Plotting ---
            # Group by Outlet and sum up monthly sales (in case of duplicate item codes in an outlet)
            monthly_sales_summary = final_item_df.groupby(['Outlet'])[month_cols].sum().reset_index()
            
            # Melt the data from wide format (Jan, Feb, Mar...) to long format (Month, Qty Sold)
            monthly_sales_melted = monthly_sales_summary.melt(
                id_vars="Outlet",
                value_vars=month_cols,
                var_name="Month",
                value_name="Qty Sold"
            )
            
            # Convert 'Month' to a proper date type for correct sorting on the chart
            monthly_sales_melted['Date'] = pd.to_datetime(monthly_sales_melted['Month'], format='%b-%Y')
            monthly_sales_melted = monthly_sales_melted.sort_values('Date')

            # Filter out zero sales for better chart visualization
            monthly_sales_melted_plot = monthly_sales_melted[monthly_sales_melted["Qty Sold"] > 0]
            
            if not monthly_sales_melted_plot.empty:
                # --- Line Chart for Monthly Trend ---
                st.markdown("### 📈 Monthly Sales Trend")
                
                # Use 'Outlet' as color if 'All Outlets' is selected
                color_var = 'Outlet' if selected_outlet == "All Outlets" else None
                
                fig = px.line(
                    monthly_sales_melted_plot,
                    x="Month",
                    y="Qty Sold",
                    color=color_var, # This generates a line for each outlet
                    markers=True,
                    title=f"Monthly Sales Quantity Trend for {selected_item_name}",
                    hover_data={"Qty Sold": True, "Month": True, "Outlet": True}
                )
                
                fig.update_layout(
                    xaxis_title="Month", 
                    yaxis_title="Quantity Sold",
                    # Ensure X-axis order is correct
                    xaxis={'categoryorder':'array', 'categoryarray': monthly_sales_melted_plot['Month'].unique().tolist()}
                )
                
                st.plotly_chart(fig, use_container_width=True)

                # --- Detailed Table (Show monthly sales) ---
                st.markdown("### 📋 Monthly Sales Breakdown")
                
                # Prepare a table showing monthly sales
                display_cols = ['Outlet'] + month_cols
                st.dataframe(
                    monthly_sales_summary[display_cols].sort_values("Outlet"),
                    use_container_width=True
                )

            else:
                st.warning(f"No sales data found for **{selected_item_name}** in the selected period/outlet(s).")
                
        else:
            st.warning("🔎 No matching items found. Try another search term.")
            
    # --- Instructions/Initial State ---
    elif not password:
        st.info("🔒 Please enter the password to access the dashboard.")

    # --- Info after access, but before search ---
    elif password == "123123" and not search_term:
        st.info("👈 Use the sidebar to filter by Outlet and the search box to find an item by Name or Barcode.")


elif password:
    st.error("❌ Incorrect Password.")
