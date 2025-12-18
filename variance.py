import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Configuration ---
# We set it to expanded by default so that when it "appears", it is already open.
st.set_page_config(
    page_title="Outlet Sales Insights", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. Initial CSS (Hide Fork and Footer) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# --- 3. Data Loading Function ---
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

# --- 4. Main Interface ---
st.title("🏪 Sales QTY Check - JAN to NOV")

# Password input
password = st.text_input("🔑 Enter Password:", type="password")

# --- 5. Dynamic Sidebar Control ---
if password == "123123":
    # CSS: Show sidebar and HIDE the close button (<<)
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: block !important;
        }
        [data-testid="sidebar-toggle"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    loaded_data = load_all_data(DATA_FILES)
    if loaded_data:
        df_combined, month_cols = loaded_data
        
        # Populate Sidebar (Only visible now)
        st.sidebar.header("Outlet Selection")
        all_outlets = sorted(df_combined['Outlet'].unique().tolist())
        selected_outlet = st.sidebar.selectbox("🏬 Select Outlet:", ["All Outlets"] + all_outlets)

        # Main Search Box
        search_input = st.text_input("🔍 Search Barcodes (Space separated):").strip()

        if search_input:
            search_terms = [t.strip() for t in search_input.split(" ") if t.strip()]
            df_base = df_combined.copy()
            if selected_outlet != "All Outlets":
                df_base = df_base[df_base["Outlet"] == selected_outlet]

            for term in search_terms:
                st.markdown("---")
                filtered = df_base[
                    df_base["Items"].astype(str).str.contains(term, case=False, na=False) |
                    df_base["Item Code"].astype(str).str.contains(term, case=False, na=False)
                ]

                if not filtered.empty:
                    unique_names = filtered['Items'].unique()
                    if len(unique_names) > 1:
                        sel_item = st.selectbox(f"Select item for '{term}':", unique_names, key=f"sel_{term}")
                        final_df = filtered[filtered['Items'] == sel_item]
                    else:
                        final_df = filtered
                        sel_item = unique_names[0]

                    st.subheader(f"📦 {sel_item}")
                    summary = final_df.groupby(['Outlet'])[month_cols].sum().reset_index()
                    melted = summary.melt(id_vars="Outlet", value_vars=month_cols, var_name="Month", value_name="Qty")
                    plot_df = melted[melted["Qty"] > 0]

                    if not plot_df.empty:
                        st.metric("Total Sold", f"{plot_df['Qty'].sum():,.0f}")
                        fig = px.bar(plot_df, x="Qty", y="Outlet", color="Month", orientation="h",
                                     category_orders={"Month": MASTER_MONTH_ORDER},
                                     color_discrete_sequence=px.colors.sequential.Blues_r)
                        
                        totals = plot_df.groupby('Outlet')['Qty'].sum().reset_index()
                        for _, r in totals.iterrows():
                            fig.add_annotation(x=r['Qty'], y=r['Outlet'], text=str(int(r['Qty'])),
                                               showarrow=False, xanchor='left', xshift=7, font=dict(weight='bold'))
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{term}")
                    else:
                        st.warning(f"No sales for {sel_item}")
                else:
                    st.error(f"❌ '{term}' not found.")
    else:
        st.error("Data files not found.")

else:
    # CSS: Hide the sidebar entirely if password is not correct
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if password:
        st.error("❌ Incorrect Password.")
    else:
        st.info("🔒 Enter password to unlock filters and data.")
