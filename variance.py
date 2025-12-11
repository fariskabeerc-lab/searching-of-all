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
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")
st.title("🏪 Sales QTY Check - Outlet Comparison") # Title updated for Bar Chart View

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
    
    # *** Calculation for Bar Chart: Total Sales ***
    # Calculate Total Sales (QTY Sold) by summing all monthly columns
    master_df['Total Sales (Qty)'] = master_df[month_cols].sum(axis=1)

    # Calculate Avg Monthly Sale (using number of months present)
    num_months_present = len(month_cols)
    if num_months_present > 0:
        master_df['Avg Monthly Sale'] = (master_df['Total Sales (Qty)'] / num_months_present).astype(int)
    else:
        master_df['Avg Monthly Sale'] = 0
    # **********************************************
        
    return master_df, month_cols

# --- Main Logic Start ---

if password == "123123":
    st.success("✅ Access Granted")
    
    # Load and merge data
    loaded_data = load_all_data(DATA_FILES)
    if loaded_data is None:
        st.stop()
        
    df_combined, month_cols = loaded_data

    # --- Sidebar: Outlet Selector (Only used to pre-filter search results) ---
    all_outlets = sorted(df_combined['Outlet'].unique().tolist())
    # Note: For the comparison bar chart, this selector acts as a way to narrow the view
    selected_outlet = st.sidebar.selectbox(
        "🏬 Select Outlet (Narrows search results only):",
        ["All Outlets"] + all_outlets
    )

    # --- Main Page: Search Box ---
    search_term = st.text_input("🔍 Search by Item Name or Barcode:").strip()

    if search_term:
        
        # 1. Apply Item Search Filter (find all rows matching the item)
        filtered_df_item = df_combined[
            df_combined["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df_combined["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ].copy()

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

            st.subheader(f"📦 Total Sales Comparison for: **{selected_item_name}**")

            # --- Group/Aggregate Data for the Bar Chart ---
            # Sum up sales by Outlet 
            outlet_sales = final_item_df.groupby('Outlet').agg(
                {'Total Sales (Qty)': 'sum', 'Avg Monthly Sale': 'mean'}
            ).reset_index()

            # --- Apply Outlet Filter (AFTER Aggregation) ---
            if selected_outlet != "All Outlets":
                outlet_sales = outlet_sales[outlet_sales["Outlet"] == selected_outlet]

            # Filter out outlets with no sales
            outlet_sales = outlet_sales[outlet_sales["Total Sales (Qty)"] > 0]
            
            if not outlet_sales.empty:
                
                # --- Overall Avg Monthly Sale for Info Box ---
                avg_sale = outlet_sales["Avg Monthly Sale"].mean()
                st.info(f"**Overall Avg Monthly Sale per Outlet:** {int(avg_sale)} units (Based on {len(month_cols)} months of data)")

                # --- Horizontal Bar Chart (Outlet Comparison) ---
                st.markdown("### 📊 Outlet Comparison (Total Sales)")
                fig = px.bar(
                    outlet_sales.sort_values("Total Sales (Qty)", ascending=True),
                    x="Total Sales (Qty)",
                    y="Outlet",
                    orientation="h",
                    text="Total Sales (Qty)",
                    color="Total Sales (Qty)",
                    color_continuous_scale="Blues",
                    hover_data={
                        "Total Sales (Qty)": True, 
                        "Avg Monthly Sale": ":.0f" # Format as integer
                    }
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(title_x=0.3, yaxis_title="Outlet", xaxis_title="Total Quantity Sold (All Months)")
                st.plotly_chart(fig, use_container_width=True)

                # --- Detailed Table ---
                st.markdown("### 📋 Outlet-wise Detailed Sales")
                st.dataframe(
                    outlet_sales[["Outlet", "Total Sales (Qty)", "Avg Monthly Sale"]]
                    .sort_values("Total Sales (Qty)", ascending=False),
                    use_container_width=True
                )

            else:
                st.warning(f"No sales data found for **{selected_item_name}** in the selected outlet(s).")
                
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
