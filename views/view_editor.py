import streamlit as st
import pandas as pd
import ast

def render():
    st.title("Stack-up Editor & Constructor")
    st.markdown("Easily view your current stack-up or add new layers using the strict Category ➔ Material ➔ Thickness logic below.")
    
    # --- 1. CURRENT STACK-UP VIEW ---
    st.subheader("1. Current PCB Layers")
    
    layers = st.session_state['stackup_data']['layers']
    df_layers = pd.DataFrame(layers)
    
    # Material Library Source Indicator
    df_lib = st.session_state.get('material_library', pd.DataFrame())
    if not df_lib.empty:
        st.caption("🌐 Material Database Source: **Google Cloud (Live via Service Account)**")
    else:
        st.error("🚨 Database Connection Failed. Please authorize the project bot.")
    
    if not df_layers.empty:
        # Display as a beautifully formatted strictly read-only dataframe
        st.dataframe(df_layers, width="stretch", hide_index=True)
    else:
        st.info("No layers in stack-up yet.")
        
    st.divider()
    
    # --- 2. ADD / EDIT LAYER FORM ---
    st.subheader("🛠️ Add New / Edit Layer")
    
    df_lib = st.session_state.get('material_library', pd.DataFrame())
    
    c1, c2, c3 = st.columns(3)
    
    # Step A: Category
    with c1:
        cat_gui = st.selectbox("1. Category", ["dielectric substrate", "metal layer", "cover"])
    
    # Filter DB logically
    valid_lib_cats = []
    if cat_gui == "dielectric substrate": valid_lib_cats = ["Core", "Prepreg"]
    elif cat_gui == "metal layer": valid_lib_cats = ["Copper Foil", "Copper"]
    else: valid_lib_cats = ["Solder Mask", "Silk Screen"]
        
    filtered_db = df_lib[df_lib['Category'].isin(valid_lib_cats)] if not df_lib.empty else pd.DataFrame()
    
    # Step B: Material Code List
    mat_options = []
    if not filtered_db.empty:
        for idx, row in filtered_db.iterrows():
            mat_options.append(f"{row.get('Brand','')} ➔ {row.get('Type/Code','')} [{row.get('Category','')}]")
    else:
        mat_options = ["⚠️ No materials found for this category"]
            
    with c2:
        selected_mat_str = st.selectbox("2. Material Type/Code", mat_options)
    
    # Step C: Intercept Thickness
    thickness_opts = []
    selected_lib_cat = "core" # default internal tag
    
    is_valid_selection = False
    if "➔" in selected_mat_str:
         import re
         match = re.search(r'➔ (.*?) \[(.*?)]', selected_mat_str)
         if match:
             code = match.group(1)
             lib_cat = match.group(2)
             is_valid_selection = True
             
             # Convert Library Category to Python Logic Types
             if lib_cat.lower() in ["core", "prepreg", "soldermask", "silkscreen"]:
                 selected_lib_cat = lib_cat.lower().replace(" ", "")
             elif "copper" in lib_cat.lower():
                 selected_lib_cat = "copper"
             elif "solder" in lib_cat.lower():
                 selected_lib_cat = "soldermask"
             
             row = filtered_db[filtered_db['Type/Code'] == code]
             if not row.empty:
                 th_str = row.iloc[0].get("Available_Thicknesses", "[]")
                 try:
                     val = ast.literal_eval(th_str) if isinstance(th_str, str) else th_str
                     if isinstance(val, list): thickness_opts = val
                 except Exception as e:
                     pass
                     
    with c3:
        if thickness_opts:
            thickness_val = st.selectbox("3. Allowed Thickness (mm)", thickness_opts)
        elif is_valid_selection:
            st.warning("⚠️ No thicknesses defined in DB for this material.")
            thickness_val = None
        else:
            st.info("Select a material first.")
            thickness_val = None

    # Step D: Submit row
    st.markdown("*(Finalize Properties)*")
    c4, c5, c6 = st.columns(3)
    with c4:
         new_id = st.text_input("Layer ID (e.g. L1, D1)", value=f"L{len(layers)+1}")
    with c5:
         new_name = st.text_input("Layer Name (Label)", value="New Layer")
    with c6:
         st.write("") # padding
         # Disable button if no valid material or thickness is selected
         button_disabled = not is_valid_selection or thickness_val is None
         if st.button("➕ Push Layer to Stack-up", type="primary", width="stretch", disabled=button_disabled):
             real_type = selected_lib_cat if cat_gui == "dielectric substrate" else ("copper" if cat_gui == "metal layer" else "soldermask")
             st.session_state['stackup_data']['layers'].append({
                 "id": new_id,
                 "name": new_name,
                 "type": real_type,
                 "thickness": thickness_val,
                 "material_ref": selected_mat_str
             })
             st.rerun()

    st.divider()
    
    # --- 3. REORDER AND DELETE ---
    st.subheader("↔️ Reorder & Remove")
    if len(layers) > 0:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sel_move_id = st.selectbox("Select Layer to affect:", [l['id'] for l in layers], key="sel_move")
        with c2:
            st.write("")
            idx = next((i for i, l in enumerate(layers) if l['id'] == sel_move_id), -1)
            if st.button("⬆️ Move Up", disabled=idx<=0, width="stretch"):
                layers[idx - 1], layers[idx] = layers[idx], layers[idx - 1]
                st.session_state['stackup_data']['layers'] = layers
                st.rerun()
        with c3:
            st.write("")
            if st.button("⬇️ Move Down", disabled=idx==len(layers)-1, width="stretch"):
                layers[idx + 1], layers[idx] = layers[idx], layers[idx + 1]
                st.session_state['stackup_data']['layers'] = layers
                st.rerun()
        with c4:
            st.write("")
            if st.button("🗑️ Delete Form", type="primary", width="stretch"):
                st.session_state['stackup_data']['layers'].pop(idx)
                st.rerun()

    st.divider()

    # --- 4. VIA EDITOR (Maintained as pure dataframe editor) ---
    st.subheader("3. Interconnect Vias")
    st.markdown("You can define Vias by specifying Start and End layers directly.")
    
    vias = st.session_state['stackup_data']['vias']
    df_vias = pd.DataFrame(vias) if vias else pd.DataFrame(columns=[
        'id', 'type', 'start_layer', 'end_layer', 'drill_diameter', 'label'
    ])
    
    layer_ids = df_layers['id'].dropna().tolist() if not df_layers.empty else []
    
    edited_df_vias = st.data_editor(
        df_vias,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.TextColumn("Via ID", required=True),
            "type": st.column_config.SelectboxColumn("Via Type", options=["PTH", "BLIND_TOP", "BLIND_BOT", "BURIED", "UVIA", "STACKED"], required=True),
            "start_layer": st.column_config.SelectboxColumn("Start Layer", options=layer_ids, required=True),
            "end_layer": st.column_config.SelectboxColumn("End Layer", options=layer_ids, required=True),
            "drill_diameter": st.column_config.NumberColumn("Drill (mm)", min_value=0.01, format="%.3f"),
            "label": st.column_config.TextColumn("Display Label")
        },
        key="vias_editor_state",
        width="stretch"
    )
    
    if st.button("💾 Apply Via Table Settings"):
        st.session_state['stackup_data']['vias'] = edited_df_vias.to_dict('records')
        st.toast("✅ Vias Saved!")
        st.rerun()
