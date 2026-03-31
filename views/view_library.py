import streamlit as st
import pandas as pd

def render():
    st.title("Material Library Database")
    st.markdown("This view renders the central materials library currently loaded from **Google Sheets**. "
                "If it fails to connect, it falls back to Mock Data automatically.")
    
    if 'material_library' in st.session_state:
        # We use a copy to compare after editing
        original_df = st.session_state['material_library']
        
        if original_df.empty:
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
        
        st.caption(f"📊 Material Database ({len(original_df)} entries)")
        
        # INTERACTIVE DATA EDITOR
        edited_df = st.data_editor(
            original_df,
            num_rows="dynamic",
            width="stretch",
            height=600,
            key="library_editor"
        )
        
        # AUTOMATIC SAVE LOGIC
        # If the edited dataframe is different from the one in session state, sync to cloud.
        if not edited_df.equals(original_df):
            from core import data_parser
            with st.status("🔄 Sincronizzazione automatica database...", expanded=False) as status:
                success = data_parser.save_material_library_to_cloud(edited_df)
                if success:
                    st.session_state['material_library'] = edited_df
                    status.update(label="✅ Database sincronizzato!", state="complete")
                    st.toast("Database Cloud aggiornato automaticamente.")
                else:
                    status.update(label="❌ Errore sincronizzazione Cloud", state="error")
    else:
        st.warning("Material Library could not be found.")
