import streamlit as st
from views import view_2d, view_library, view_editor, view_3d
from core import data_parser
from core import auth

# Configuration MUST be the first Streamlit command
st.set_page_config(
    page_title="PCB Stack-up & Via Visualizer",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize necessary Streamlit session state variables safely."""
    if 'material_library' not in st.session_state:
        # Load external or mock library
        st.session_state['material_library'] = data_parser.get_material_library()

    # Dummy JSON-like stack-up data dictionary (2 metal layers, 1 dielectric core, 1 through-hole via)
    if 'stackup_data' not in st.session_state:
        st.session_state['stackup_data'] = {
            "layers": [
                {
                    "id": "L1",
                    "name": "Top Copper",
                    "type": "metal",
                    "material_ref": "Generic Copper",
                    "thickness": 0.035, # mm
                    "color_hex": "#CC5500" # Orange Shades for metals
                },
                {
                    "id": "D1",
                    "name": "FR4 Core",
                    "type": "dielectric",
                    "material_ref": "Generic FR4",
                    "thickness": 1.5, # mm
                    "color_hex": "#708090" # Matte Earth Tones for dielectrics
                },
                {
                    "id": "L2",
                    "name": "Bottom Copper",
                    "type": "metal",
                    "material_ref": "Generic Copper",
                    "thickness": 0.035, # mm
                    "color_hex": "#CC5500" # Orange Shades
                }
            ],
            "vias": [
                {
                    "id": "VIA_TH_1",
                    "type": "PTH",
                    "start_layer": "L1",
                    "end_layer": "L2",
                    "drill_diameter": 0.3, # mm
                    "label": "PTH\nL1-L2"
                }
            ]
        }
    
    # UI Toggles and Controls State Initialization
    if 'show_labels' not in st.session_state:
        st.session_state['show_labels'] = True
    
    if 'show_left_labels' not in st.session_state:
        st.session_state['show_left_labels'] = False
    
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = '2D Cross-Section'
        
    if 'explosion_factor' not in st.session_state:
        st.session_state['explosion_factor'] = 0.0

def build_sidebar():
    """Create the sidebar with UI toggles."""
    st.sidebar.title("Visualizer Controls")
    
    # User Session Information (Native Auth)
    if st.user.is_logged_in:
        username = st.user.name if st.user.name else st.user.email
        st.sidebar.write(f"Logged in as: **{username}**")
        if st.sidebar.button("Logout", type="secondary"):
            auth.logout()
        
    st.sidebar.divider()
    
    st.session_state['show_labels'] = st.sidebar.toggle(
        "Show Right Labels", 
        value=st.session_state.get('show_labels', True),
        help="Toggle layer and via dimensional labels on the right."
    )
    
    st.session_state['show_left_labels'] = st.sidebar.toggle(
        "Show Left Labels", 
        value=st.session_state.get('show_left_labels', False),
        help="Toggle layer thickness annotations on the left side."
    )
    
    st.session_state['view_mode'] = st.sidebar.radio(
        "View Mode", 
        options=['Stack-up Editor', 'Material Library', '2D Cross-Section', '3D Exploded View'], 
        index=0 if st.session_state['view_mode'] == 'Stack-up Editor' else (2 if st.session_state['view_mode'] == '2D Cross-Section' else (3 if st.session_state['view_mode'] == '3D Exploded View' else 1))
    )
    
    st.sidebar.subheader("3D Controls")
    st.session_state['explosion_factor'] = st.sidebar.slider(
        "3D Explosion Slider", 
        min_value=0.0, 
        max_value=10.0, 
        value=st.session_state['explosion_factor'], 
        step=0.1,
        help="Control the separation distance between layers in the 3D view.",
        disabled=(st.session_state['view_mode'] != '3D Exploded View')
    )
    
    st.sidebar.divider()
    st.sidebar.subheader("📁 Project I/O")
    
    import json
    json_str = json.dumps(st.session_state.get('stackup_data', {}), indent=4)
    st.sidebar.download_button("💾 Export Project (JSON)", data=json_str, file_name="pcb_stackup.json", mime="application/json", width="stretch")
    
    uploaded_file = st.sidebar.file_uploader("📂 Load Project (.json)", type=["json"], key="json_uploader")
    if uploaded_file is not None:
         if st.sidebar.button("📥 Import JSON", use_container_width=True):
             try:
                 data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                 if "layers" in data and "vias" in data:
                     st.session_state['stackup_data'] = data
                     st.sidebar.success("Project Imported!")
                     st.rerun()
                 else:
                     st.sidebar.error("Invalid Format")
             except Exception as e:
                 st.sidebar.error(f"Error: {e}")
    
    st.sidebar.divider()
    st.sidebar.subheader("☁️ Cloud Project Manager")
    
    # 1. Project Selection (Load/Delete)
    project_list = data_parser.get_project_list()
    selected_project = st.sidebar.selectbox("📂 Existing Projects", options=["-- New Project --"] + project_list)
    
    # 2. Project Name Input
    default_name = selected_project if selected_project != "-- New Project --" else ""
    proj_name = st.sidebar.text_input("📝 Project Name", value=default_name, key="cloud_proj_name")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True, help="Create or Overwrite project in Cloud"):
            if proj_name:
                if data_parser.save_stackup_to_cloud(proj_name, st.session_state['stackup_data']):
                    st.toast(f"✅ {proj_name} Saved!")
                    st.rerun()
            else:
                st.sidebar.error("Enter a Name")
                
    with col2:
        if st.button("📡 Load", use_container_width=True, disabled=(selected_project == "-- New Project --")):
            loaded_data = data_parser.load_project_from_cloud(selected_project)
            if loaded_data:
                st.session_state['stackup_data'] = loaded_data
                st.toast(f"✅ {selected_project} Loaded!")
                st.rerun()

    if st.sidebar.button("🗑️ Delete from Cloud", use_container_width=True, type="secondary", disabled=(selected_project == "-- New Project --")):
        if data_parser.delete_project_from_cloud(selected_project):
            st.toast(f"🗑️ {selected_project} Deleted")
            st.rerun()

def main():
    # 0. Check Login
    if not auth.check_login():
        return
        
    # 1. State initialization
    init_session_state()
    
    # 2. Sidebar controls
    build_sidebar()
    
    # 3. Main layout
    st.title("PCB Stack-up & Via Visualizer")
    
    # Routing logic based on view mode
    if st.session_state['view_mode'] == 'Stack-up Editor':
        view_editor.render()
    elif st.session_state['view_mode'] == 'Material Library':
        view_library.render()
    elif st.session_state['view_mode'] == '2D Cross-Section':
        view_2d.render()
    elif st.session_state['view_mode'] == '3D Exploded View':
        view_3d.render()

if __name__ == "__main__":
    main()
