import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Setup ---
st.set_page_config(page_title="Outlet Sales Insights", layout="wide")

# Initialize state for the sidebar toggle
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True

# --- 2. CSS Hack: Hide Fork & Control Sidebar Visibility ---
# This CSS hides the "fork" (header) and the footer.
# It also hides the sidebar based on our custom button state.
sidebar_display = "block" if st.session_state.show_sidebar else "none"

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{
        display: {sidebar_display};
    }}
    /* Hide the default small toggle arrow */
    [data-testid="sidebar-toggle"] {{display: none;}}
    .block-container {{padding-top: 1rem;}}
    </style>
""", unsafe_allow_html=True)

# --- 3. Sidebar Toggle Function ---
def toggle_sidebar():
    st.session_state.show_sidebar = not st.session_state.show_sidebar

# --- 4. Main Page Top Bar ---
# Separate button to open/close
st.button("📁 Open/Close Filter Bar", on_click=toggle_sidebar)

st.title("🏪 Sales QTY Check - JAN to NOV")

# --- 5. Configuration & Data Loading ---
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
        except:
            continue
    if not data_frames: return None
    master_df = pd.concat(data_frames, ignore_index=True)
    if 'Company Name' in master_df.columns:
        master_df = master_df.rename(columns={'Company Name': 'Outlet'})
    month_cols = [c for c in master_df.columns if c in MASTER_MONTH_ORDER] 
    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)
    return master_df, month_cols

# --- 6. Authentication ---
# 'key' is vital here - it prevents the password from clearing when the sidebar toggles
password = st.text_input("🔑 Enter Password:", type="password", key="app_password")

if password == "123123":
    loaded_data = load_all_data(DATA_FILES)
    if loaded_data:
        df_combined, month_cols = loaded_data
        
        # --- Sidebar Filters ---
        all_outlets = sorted(df_combined['Outlet'].unique().tolist())
        selected_outlet = st.sidebar.selectbox("🏬 Select Outlet:", ["All Outlets"] + all_outlets)

        # --- Multi-Barcode Search ---
        # User types: "89011 89022 89033"
        search_input = st.text_input("🔍 Search Barcodes (Separated by Space):", key="search_bar").strip()

        if search_input:
            # Split search by space to handle multiple items one by one
            search_terms = [t.strip() for t in search_input.split(" ") if t.strip()]
            
            df_base = df_combined.copy()
            if selected_outlet != "All Outlets":
                df_base = df_base[df_base["Outlet"] == selected_outlet]

            for term in search_terms:
                st.markdown(f"---")
                st.subheader(f"🔍 Search Result for: `{term}`")
                
                filtered = df_base[
                    df_base["Items"].astype(str).str.contains(term, case=False, na=False) |
                    df_base["Item Code"].astype(str).str.contains(term, case=False, na=False)
                ]

                if not filtered.empty:
                    # Logic to handle if one barcode/term matches multiple items
                    unique_names = filtered['Items'].unique()
                    if len(unique_names) > 1:
                        sel_item = st.selectbox(f"Select specific item for '{term}':", unique_names, key=f"sel_{term}")
                        final_df = filtered[filtered['Items'] == sel_item]
                    else:
                        final_df = filtered
                        sel_item = unique_names[0]

                    # Summary Calculations
                    summary = final_df.groupby(['Outlet'])[month_cols].sum().reset_index()
                    melted = summary.melt(id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty")
                    plot_df = melted[melted["Qty"] > 0]

                    if not plot_df.empty:
                        st.metric(f"Total QTY Sold ({sel_item})", f"{plot_df['Qty'].sum():,.0f} units")
                        
                        # Build Chart
                        fig = px.bar(plot_df, x="Qty", y="Outlet", color="Month", orientation="h",
                                     title=f"Monthly Sales: {sel_item}",
                                     category_orders={"Month": MASTER_MONTH_ORDER},
                                     color_discrete_sequence=px.colors.sequential.Blues_r)
                        
                        # Value labels
                        totals = plot_df.groupby('Outlet')['Qty'].sum().reset_index()
                        for _, r in totals.iterrows():
                            fig.add_annotation(x=r['Qty'], y=r['Outlet'], text=str(int(r['Qty'])),
                                               showarrow=False, xanchor='left', xshift=7, font=dict(weight='bold'))
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{term}")
                    else:
                        st.warning(f"No sales recorded for: {sel_item}")
                else:
                    st.error(f"❌ Barcode/Item '{term}' not found in data.")
    else:
        st.error("Missing Data: Ensure Excel files are in the same folder.")

elif password:
    st.error("❌ Incorrect Password.")
else:
    st.info("🔒 Please enter the password to access.")
