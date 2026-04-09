import streamlit as st
from views import view_2d, view_library, view_editor, view_3d
from core import data_parser
from core import auth
from core import hfss_exporter
from core import color_manager

# Configuration MUST be the first Streamlit command
st.set_page_config(
    page_title="PCB Stack-up & Via Visualizer",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

VIEW_MODES = ['Stack-up Editor', '2D Cross-Section', '3D Exploded View', 'Material Library']


def init_session_state():
    """Initialize necessary Streamlit session state variables safely."""
    color_manager.ensure_palette_state(st.session_state)

    if 'material_library' not in st.session_state:
        # Load external or mock library
        st.session_state['material_library'] = data_parser.get_material_library()

    metal_color = color_manager.get_role_color(st.session_state, 'metal')
    core_color = color_manager.get_role_color(st.session_state, 'core')

    # Dummy JSON-like stack-up data dictionary (2 metal layers, 1 dielectric core, 1 through-hole via)
    # NOTE: Layers are ordered TOP-DOWN in the list (index 0 = top), but IDs are numbered BOTTOM-UP
    # So L1 = Bottom Copper, D1 = Core, L2 = Top Copper
    if 'stackup_data' not in st.session_state:
        st.session_state['stackup_data'] = {
            "layers": [
                {
                    "id": "L2",
                    "name": "L2 - Top Copper",
                    "type": "metal",
                    "material_ref": "Generic Copper",
                    "thickness": 0.035, # mm
                    "color_hex": metal_color,
                    "color_source": "palette",
                    "palette_role": "metal"
                },
                {
                    "id": "D1",
                    "name": "D1 - FR4 Core",
                    "type": "dielectric",
                    "material_ref": "Generic FR4",
                    "thickness": 1.5, # mm
                    "color_hex": core_color,
                    "color_source": "palette",
                    "palette_role": "core"
                },
                {
                    "id": "L1",
                    "name": "L1 - Bottom Copper",
                    "type": "metal",
                    "material_ref": "Generic Copper",
                    "thickness": 0.035, # mm
                    "color_hex": metal_color,
                    "color_source": "palette",
                    "palette_role": "metal"
                }
            ],
            "vias": [
                {
                    "id": "VIA_TH_1",
                    "name": "PTH L2-L1",
                    "type": "PTH",
                    "start_layer": "L2",
                    "end_layer": "L1",
                    "drill_diameter": 0.3, # mm
                    "label": "PTH\nL2-L1"
                }
            ]
        }
    
    # UI Toggles and Controls State Initialization
    if 'show_id' not in st.session_state:
        st.session_state['show_id'] = True

    if 'show_name' not in st.session_state:
        st.session_state['show_name'] = True
    
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = 'Stack-up Editor'
    elif st.session_state['view_mode'] not in VIEW_MODES:
        st.session_state['view_mode'] = 'Stack-up Editor'

    if 'explosion_factor' not in st.session_state:
        st.session_state['explosion_factor'] = 0.0

def build_sidebar():
    """Create the sidebar with UI toggles."""
    st.sidebar.title("Visualizer Controls")
    
    # User Session Information
    if st.session_state.get('logged_in'):
        username = st.session_state.get('user_name', 'Unknown User')
        st.sidebar.write(f"Logged in as: **{username}**")
        if st.sidebar.button("Logout", type="secondary"):
            auth.logout()
        
    st.sidebar.divider()

    st.session_state['show_id'] = st.sidebar.toggle(
        "Show ID",
        value=st.session_state.get('show_id', True),
        help="Toggle layer ID display on the left side."
    )

    st.session_state['show_name'] = st.sidebar.toggle(
        "Show Name",
        value=st.session_state.get('show_name', True),
        help="Toggle layer name display on the left side."
    )
    
    current_view = st.session_state.get('view_mode', 'Stack-up Editor')
    if current_view not in VIEW_MODES:
        current_view = 'Stack-up Editor'

    st.session_state['view_mode'] = st.sidebar.radio(
        "View Mode",
        options=VIEW_MODES,
        index=VIEW_MODES.index(current_view)
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

    color_manager.ensure_palette_state(st.session_state)
    palette_names = color_manager.get_palette_names()
    current_palette_name = color_manager.get_active_palette_name(st.session_state)
    selected_palette_name = st.sidebar.selectbox(
        "🎨 Active Palette",
        options=palette_names,
        index=palette_names.index(current_palette_name),
        help="Apply the selected palette to palette-linked layers in both the 2D and 3D views.",
        key="sidebar_active_palette_selector"
    )

    if selected_palette_name != current_palette_name:
        color_manager.set_active_palette(st.session_state, selected_palette_name)
        color_manager.apply_palette_to_stackup(st.session_state, keep_custom=True)
        st.toast(f"🎨 Palette switched to {selected_palette_name}")

    st.sidebar.caption("Applies to both `2D Cross-Section` and `3D Exploded View`.")
    
    st.sidebar.divider()
    st.sidebar.subheader("📁 Project I/O")

    import json
    json_str = json.dumps(st.session_state.get('stackup_data', {}), indent=4)
    st.sidebar.download_button("💾 Export Project (JSON)", data=json_str, file_name="pcb_stackup.json", mime="application/json", width="stretch")

    # HFSS Script Export
    if st.sidebar.button("📜 Export HFSS Script", use_container_width=True):
        try:
            hfss_script = hfss_exporter.generate_hfss_script(st.session_state['stackup_data'])
            st.sidebar.download_button(
                "⬇️ Download HFSS Script",
                data=hfss_script,
                file_name="pcb_stackup_hfss.py",
                mime="text/plain",
                width="stretch"
            )
            st.sidebar.success("✅ Script generated!")
        except Exception as e:
            st.sidebar.error(f"❌ Error generating script: {e}")
    
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
    elif st.session_state['view_mode'] == '2D Cross-Section':
        view_2d.render()
    elif st.session_state['view_mode'] == '3D Exploded View':
        view_3d.render()
    elif st.session_state['view_mode'] == 'Material Library':
        view_library.render()

if __name__ == "__main__":
    main()
