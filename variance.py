import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config & Session State ---
# This must be the very first Streamlit command
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.set_page_config(
    page_title="Outlet Sales Insights", 
    layout="wide", 
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- Hide Header/Fork/Footer ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

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
        except Exception:
            return None
    if not data_frames: return None
    master_df = pd.concat(data_frames, ignore_index=True)
    if 'Company Name' in master_df.columns:
        master_df = master_df.rename(columns={'Company Name': 'Outlet'})
    month_cols = [c for c in master_df.columns if c in MASTER_MONTH_ORDER] 
    for col in month_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce').fillna(0)
    return master_df, month_cols

# --- Sidebar Toggle Logic ---
def toggle_sidebar():
    if st.session_state.sidebar_state == "expanded":
        st.session_state.sidebar_state = "collapsed"
    else:
        st.session_state.sidebar_state = "expanded"
    st.rerun()

# --- App Interface ---
col1, col2 = st.columns([0.2, 0.8])
with col1:
    # This button handles the open/close action
    st.button("📁 Open/Close Filter Bar", on_click=toggle_sidebar)

st.title("🏪 Sales QTY Check - JAN to NOV")

# Adding a KEY to password keeps it logged in even when sidebar toggles
password = st.text_input("🔑 Enter Password:", type="password", key="saved_password")

if password == "123123":
    loaded_data = load_all_data(DATA_FILES)
    if loaded_data:
        df_combined, month_cols = loaded_data
        
        # Sidebar Content
        all_outlets = sorted(df_combined['Outlet'].unique().tolist())
        selected_outlet = st.sidebar.selectbox("🏬 Select Outlet:", ["All Outlets"] + all_outlets)

        # Adding a KEY to search keeps the text there when sidebar toggles
        search_input = st.text_input("🔍 Search Barcodes (space separated):", key="search_val").strip()

        if search_input:
            search_terms = [t.strip() for t in search_input.split(" ") if t.strip()]
            
            df_base = df_combined.copy()
            if selected_outlet != "All Outlets":
                df_base = df_base[df_base["Outlet"] == selected_outlet]

            for term in search_terms:
                st.markdown(f"---")
                filtered = df_base[
                    df_base["Items"].astype(str).str.contains(term, case=False, na=False) |
                    df_base["Item Code"].astype(str).str.contains(term, case=False, na=False)
                ]

                if not filtered.empty:
                    # Handle multiple items found for one term
                    unique_items = filtered['Items'].unique()
                    if len(unique_items) > 1:
                        selected_item = st.selectbox(f"Found multiple for '{term}':", unique_items, key=f"sel_{term}")
                        final_df = filtered[filtered['Items'] == selected_item]
                    else:
                        final_df = filtered
                        selected_item = unique_items[0]

                    st.subheader(f"📦 Item: {selected_item}")
                    
                    # Calculations
                    m_summary = final_df.groupby(['Outlet'])[month_cols].sum().reset_index()
                    m_melted = m_summary.melt(id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty")
                    m_plot = m_melted[m_melted["Qty"] > 0]

                    if not m_plot.empty:
                        st.metric("Total Sold", f"{m_plot['Qty'].sum():,.0f} units")
                        
                        # Chart
                        fig = px.bar(m_plot, x="Qty", y="Outlet", color="Month", orientation="h",
                                     category_orders={"Month": MASTER_MONTH_ORDER},
                                     color_discrete_sequence=px.colors.sequential.Blues_r)
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        
                        # Add value labels
                        totals = m_plot.groupby('Outlet')['Qty'].sum().reset_index()
                        for _, r in totals.iterrows():
                            fig.add_annotation(x=r['Qty'], y=r['Outlet'], text=str(int(r['Qty'])),
                                               showarrow=False, xanchor='left', xshift=5)
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"ch_{term}")
                    else:
                        st.warning(f"No sales found for {term}")
                else:
                    st.error(f"Item code '{term}' not found.")
    else:
        st.error("Data files not found. Please check filenames.")

elif password:
    st.error("❌ Incorrect Password.")
else:
    st.info("🔒 Please enter password.")
    
