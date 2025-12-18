import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")

# --- CUSTOM CSS TO HIDE THE RIGHT-SIDE TOOLBAR ONLY ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏪 Sales QTY Check -JAN to NOV")

# --- Password Protection ---
password = st.text_input("🔑 Enter Password:", type="password")

# --- Configuration ---
DATA_FILES = ["Month wise full outlet sales(1).xlsx", "Month wise full outlet sales.Xlsx"]
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
    
    all_cols = master_df.columns.tolist()
    month_cols = [c for c in all_cols if c in MASTER_MONTH_ORDER] 
    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)
        
    return master_df, month_cols

if password == "123123":
    st.success("✅ Access Granted")
    loaded_data = load_all_data(DATA_FILES)
    if loaded_data is None: st.stop()
    df_combined, month_cols = loaded_data

    # --- Sidebar ---
    all_outlets = sorted(df_combined['Outlet'].unique().tolist())
    selected_outlet = st.sidebar.selectbox("🏬 Select Outlet:", ["All Outlets"] + all_outlets)

    # --- Search Box ---
    search_input = st.text_input("🔍 Search (separate multiple with space):").strip()

    if search_input:
        search_terms = [term.strip() for term in search_input.split() if term.strip()]
        search_pattern = "|".join(search_terms)
        
        df_filtered = df_combined if selected_outlet == "All Outlets" else df_combined[df_combined["Outlet"] == selected_outlet]
        
        filtered_df_item = df_filtered[
            df_filtered["Items"].astype(str).str.contains(search_pattern, case=False, na=False) |
            df_filtered["Item Code"].astype(str).str.contains(search_pattern, case=False, na=False)
        ]

        if not filtered_df_item.empty:
            unique_items = filtered_df_item['Items'].unique()

            for selected_item_name in unique_items:
                st.divider()
                final_item_df = filtered_df_item[filtered_df_item['Items'] == selected_item_name]
                st.subheader(f"📦 Breakdown: **{selected_item_name}**")
                
                # Data Prep
                monthly_sales_summary = final_item_df.groupby(['Outlet'])[month_cols].sum().reset_index()
                monthly_sales_melted = monthly_sales_summary.melt(
                    id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty Sold"
                )
                plot_data = monthly_sales_melted[monthly_sales_melted["Qty Sold"] > 0]
                
                if not plot_data.empty:
                    st.metric("🏆 GRAND TOTAL", f"{plot_data['Qty Sold'].sum():,.0f} units")
                    
                    # --- Chart with Monthly Segment Labels ---
                    present_month_order = [m for m in MASTER_MONTH_ORDER if m in plot_data['Month'].unique()]
                    
                    fig = px.bar(
                        plot_data,
                        x="Qty Sold",
                        y="Outlet",
                        color="Month",
                        text="Qty Sold", # This shows the total for EACH month segment
                        orientation="h",
                        title=f"Sales by Outlet & Month: {selected_item_name}",
                        color_discrete_sequence=px.colors.sequential.Blues_r,
                        category_orders={"Month": present_month_order}
                    )
                    
                    # Format the text inside segments
                    fig.update_traces(texttemplate='%{text:.0f}', textposition='inside')
                    fig.update_traces(marker_line_width=1, marker_line_color='black')

                    # --- Add Grand Total at the very end of the bar ---
                    outlet_totals = plot_data.groupby('Outlet')['Qty Sold'].sum().reset_index()
                    for _, row in outlet_totals.iterrows():
                        fig.add_annotation(
                            x=row['Qty Sold'], y=row['Outlet'],
                            text=f"<b>Sum: {row['Qty Sold']:.0f}</b>",
                            showarrow=False, xanchor='left', xshift=10, font=dict(size=12, color='blue')
                        )

                    fig.update_layout(
                        xaxis_title="Quantity Sold", yaxis_title="Outlet",
                        yaxis={'categoryorder':'total ascending'},
                        margin=dict(r=150) # Extra space for the sum labels
                    )

                    st.plotly_chart(fig, use_container_width=True, key=f"c_{selected_item_name}")
                else:
                    st.warning(f"No sales found for {selected_item_name}")
        else:
            st.warning("🔎 No items found.")

elif password:
    st.error("❌ Incorrect Password.")
