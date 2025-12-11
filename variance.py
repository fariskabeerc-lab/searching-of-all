import streamlit as st
import pandas as pd
import plotly.express as px
from functools import reduce




# --- Page Config ---
st.set_page_config(page_title="Monthly Sales Insights", layout="wide")
st.title("🗓️ Sales QTY Check - Monthly Trend")

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Configuration (Update with your actual file names) ---
# Assuming your new datasets have the monthly columns and an 'Outlet' column
DATA_FILES = {
    "Outlet A Sales": "Dataset1_OutletA_monthly.xlsx",
    "Outlet B Sales": "Dataset2_OutletB_monthly.xlsx",
    # Add more files as needed
}

# --- Cache Data Loading and Merging ---
@st.cache_data
def load_all_data(files_dict):
    data_frames = []
    
    # 1. Load each dataset and add an 'Outlet' column based on the key
    for outlet_name, file_path in files_dict.items():
        try:
            df = pd.read_excel(file_path)
            # Standardize column names
            df.columns = df.columns.str.strip()
            
            # Use the key from the dictionary as the 'Outlet' name
            df['Outlet'] = outlet_name
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
    # We will assume that 'Item Code' and 'Items' are the common keys
    master_df = pd.concat(data_frames, ignore_index=True)
    
    # 3. Clean up data types and select relevant columns
    
    # List of all expected monthly columns
    MONTHLY_COLUMNS = [f"{m}-{y}" for y in ["2025"] for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]]
    
    # Filter for the actual monthly columns present in the data
    month_cols = [c for c in master_df.columns if any(m in c for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])]
    
    required_cols = ['Outlet', 'Item Code', 'Items'] + month_cols
    
    # Ensure all required columns exist before proceeding
    master_df = master_df.reindex(columns=required_cols, fill_value=0)
    
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
        st.stop() # Stop if data loading failed
        
    df_combined, month_cols = loaded_data

    # --- Sidebar: Outlet Selector ---
    all_outlets = sorted(df_combined['Outlet'].unique().tolist())
    selected_outlet = st.sidebar.selectbox(
        "🏬 Select Outlet:",
        ["All Outlets"] + all_outlets
    )

    # --- Sidebar: Item Code/Name Search Box ---
    search_term = st.text_input("🔍 Search by Item Name or Barcode:").strip()

    if search_term:
        
        # --- Apply Outlet Filter FIRST ---
        if selected_outlet != "All Outlets":
            df_filtered = df_combined[df_combined["Outlet"] == selected_outlet].copy()
        else:
            df_filtered = df_combined.copy()
            
        # --- Apply Item Search Filter ---
        filtered_df_item = df_filtered[
            df_filtered["Items"].astype(str).str.contains(search_term, case=False, na=False)
            | df_filtered["Item Code"].astype(str).str.contains(search_term, case=False, na=False)
        ]

        if not filtered_df_item.empty:
            
            # If multiple items match, let the user select one for the graph
            if len(filtered_df_item) > 1:
                item_options = filtered_df_item['Items'].unique()
                selected_item_name = st.selectbox("Select specific item:", item_options)
                final_item_df = filtered_df_item[filtered_df_item['Items'] == selected_item_name]
            else:
                final_item_df = filtered_df_item
                selected_item_name = final_item_df.iloc[0]["Items"]

            st.subheader(f"📦 Results for: **{selected_item_name}**")
            
            # --- Melt data for Time Series Plotting ---
            # Group by Outlet and sum up monthly sales (important if multiple rows for same item/outlet exist)
            monthly_sales_summary = final_item_df.groupby(['Outlet'])[month_cols].sum().reset_index()
            
            monthly_sales_melted = monthly_sales_summary.melt(
                id_vars="Outlet",
                value_vars=month_cols,
                var_name="Month",
                value_name="Qty Sold"
            )
            
            # Convert 'Month' to a proper date type for correct sorting on the chart
            monthly_sales_melted['Date'] = pd.to_datetime(monthly_sales_melted['Month'], format='%b-%Y')
            monthly_sales_melted = monthly_sales_melted.sort_values('Date')

            # Filter out zero sales for better chart visualization (optional)
            monthly_sales_melted = monthly_sales_melted[monthly_sales_melted["Qty Sold"] > 0]
            
            if not monthly_sales_melted.empty:
                # --- Line Chart for Monthly Trend ---
                st.markdown("### 📈 Monthly Sales Trend")
                
                # Check if we are showing all outlets or a single one
                color_var = 'Outlet' if selected_outlet == "All Outlets" else None
                
                fig = px.line(
                    monthly_sales_melted,
                    x="Month",
                    y="Qty Sold",
                    color=color_var,
                    markers=True,
                    title=f"Monthly Sales Quantity for {selected_item_name}",
                    hover_data={"Qty Sold": True, "Month": True, "Outlet": True}
                )
                
                fig.update_layout(
                    xaxis_title="Month", 
                    yaxis_title="Quantity Sold",
                    xaxis={'categoryorder':'array', 'categoryarray': monthly_sales_melted['Month'].unique().tolist()}
                )
                
                st.plotly_chart(fig, use_container_width=True)

                # --- Detailed Table (Show pivot for better view) ---
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
