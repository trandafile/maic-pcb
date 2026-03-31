import streamlit as st
import pandas as pd

def render():
    st.title("Material Library Database")
    st.markdown("This view renders the central materials library currently loaded from **Google Sheets**. "
                "If it fails to connect, it falls back to Mock Data automatically.")
    
    if 'material_library' in st.session_state:
        df = st.session_state['material_library']
        
        if df.empty:
            st.info("💡 The Cloud database appears to be empty.")
            if st.button("🌱 Initialize with Sample Materials", use_container_width=True):
                mock_data = [
                    {"Brand": "Isola", "Type/Code": "370HR", "Category": "Core", "Er": 4.1, "Df": 0.015, "Available_Thicknesses": "[0.1, 0.2, 0.5, 1.0, 1.5]"},
                    {"Brand": "Isola", "Type/Code": "370HR P", "Category": "Prepreg", "Er": 4.1, "Df": 0.015, "Available_Thicknesses": "[0.05, 0.1, 0.2]"},
                    {"Brand": "Rogers", "Type/Code": "4350B", "Category": "Core", "Er": 3.48, "Df": 0.0037, "Available_Thicknesses": "[0.254, 0.508, 0.762]"},
                    {"Brand": "Generic Copper", "Type/Code": "1oz", "Category": "Copper Foil", "Er": None, "Df": None, "Available_Thicknesses": "[0.035]"}
                ]
                st.session_state['material_library'] = pd.DataFrame(mock_data)
                st.rerun()
        
        c1, c2 = st.columns([4, 1])
        with c1:
             st.caption(f"Total Database Entries: {len(df)}")
        with c2:
             from core import data_parser
             if not df.empty and st.button("🔌 Sync Library to Cloud", type="primary", use_container_width=True):
                 if data_parser.save_material_library_to_cloud(df):
                     st.toast("✅ Library updated on Google Sheets!")
        
        if not df.empty:
            st.dataframe(df, width="stretch", height=600)
    else:
        st.warning("Material Library could not be found.")
