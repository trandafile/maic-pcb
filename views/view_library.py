import pandas as pd
import streamlit as st

from core import color_manager, data_parser


def _render_material_library_editor():
    if 'material_library' not in st.session_state:
        st.warning("Material Library could not be found.")
        return

    original_df = st.session_state['material_library']

    if original_df.empty:
        st.info("💡 The Cloud database appears to be empty.")
        if st.button("🌱 Initialize with Sample Materials", use_container_width=True, key="init_sample_materials"):
            mock_data = [
                {"Brand": "Isola", "Type/Code": "370HR", "Category": "core", "Er": 4.1, "Df": 0.015, "Available_Thicknesses": "[0.1, 0.2, 0.5, 1.0, 1.5]"},
                {"Brand": "Isola", "Type/Code": "370HR P", "Category": "prepreg", "Er": 4.1, "Df": 0.015, "Available_Thicknesses": "[0.05, 0.1, 0.2]"},
                {"Brand": "Rogers", "Type/Code": "4350B", "Category": "core", "Er": 3.48, "Df": 0.0037, "Available_Thicknesses": "[0.254, 0.508, 0.762]"},
                {"Brand": "Generic Copper", "Type/Code": "1oz", "Category": "copper", "Er": None, "Df": None, "Available_Thicknesses": "[0.035]"}
            ]
            mock_df = pd.DataFrame(mock_data)
            if data_parser.save_material_library_to_cloud(mock_df):
                st.session_state['material_library'] = mock_df
                st.toast("✅ Sample Library synchronized to Cloud!")
                st.rerun()
            else:
                st.error("❌ Failed to initialize Cloud database. Check your connection/secrets.")

    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption(f"📊 Material Database ({len(original_df)} entries)")
    with c2:
        if not original_df.empty and st.button("🔌 Force Sync", type="secondary", use_container_width=True, key="force_sync_material_library"):
            if data_parser.save_material_library_to_cloud(original_df):
                st.toast("✅ Force sync successful!")

    column_config = {
        "Category": st.column_config.SelectboxColumn(
            "Category",
            help="Select the material category",
            options=["copper", "core", "prepreg"],
            required=True,
            width="medium"
        )
    }

    edited_df = st.data_editor(
        original_df,
        num_rows="dynamic",
        width="stretch",
        height=450,
        key="library_editor",
        column_config=column_config
    )

    if not edited_df.equals(original_df):
        with st.status("🔄 Automatic material-library sync...", expanded=False) as status:
            success = data_parser.save_material_library_to_cloud(edited_df)
            if success:
                st.session_state['material_library'] = edited_df
                status.update(label="✅ Material library synchronized!", state="complete")
                st.toast("Material library updated automatically.")
            else:
                status.update(label="❌ Cloud synchronization error", state="error")


def _render_palette_editor():
    color_manager.ensure_palette_state(st.session_state)
    current_palette_name = color_manager.get_active_palette_name(st.session_state)
    palette_names = color_manager.get_palette_names()

    st.subheader("🎨 Color Palette Editor")
    st.caption("The global palette is based on four linked slots: `Col#1` metal, `Col#2` dielectric core, `Col#3` prepreg, `Col#4` cover. Custom layer colors remain unchanged.")
    st.info(f"Active palette for the 2D/3D views: **{current_palette_name}** — change it from the left sidebar.")

    edit_palette_name = st.selectbox(
        "Palette to Edit",
        palette_names,
        index=palette_names.index(current_palette_name),
        key="palette_editor_target_name",
        help="This dropdown selects which palette definition you want to edit. It does not change the active 2D/3D palette.",
    )

    palette_colors = color_manager.get_palette_colors(st.session_state, edit_palette_name)
    preset_options = color_manager.build_preset_options(st.session_state, palette_name=edit_palette_name)
    edited_colors = {}

    col1, col2 = st.columns(2)
    for idx, preset in enumerate(preset_options):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            st.markdown(f"**Col#{preset['number']} - {preset['display_name']}**")
            st.caption(f"{preset['name']} · {preset['hex']}")
            edited_colors[preset['role']] = st.color_picker(
                f"Color {preset['number']}",
                value=palette_colors.get(preset['role'], preset['hex']),
                key=f"palette_editor_{edit_palette_name}_{preset['role']}",
                label_visibility="collapsed",
            )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Apply Palette to Stack-up", use_container_width=True, type="primary", key="apply_palette_to_stackup"):
            for role, color_hex in edited_colors.items():
                color_manager.update_palette_color(st.session_state, edit_palette_name, role, color_hex)

            if edit_palette_name == current_palette_name:
                color_manager.set_active_palette(st.session_state, current_palette_name)
                color_manager.apply_palette_to_stackup(st.session_state, keep_custom=True)
                st.toast("✅ Active palette updated and applied to the stack-up")
            else:
                st.toast(f"✅ Saved changes to {edit_palette_name}. Select it in the left sidebar to apply it.")
            st.rerun()

    with c2:
        if st.button("Reset Palette Colors", use_container_width=True, type="secondary", key="reset_palette_defaults"):
            color_manager.reset_palette_colors(st.session_state, edit_palette_name)
            if edit_palette_name == current_palette_name:
                color_manager.set_active_palette(st.session_state, current_palette_name)
                color_manager.apply_palette_to_stackup(st.session_state, keep_custom=True)
            st.toast(f"↺ {edit_palette_name} palette reset to its defaults")
            st.rerun()


def render(show_title=True, show_palette_editor=True, embedded=False):
    if show_title:
        st.title("Material Library")
        st.markdown("This section renders the central materials library currently loaded from **Google Sheets**.")
    else:
        st.subheader("Material Library")
        if embedded:
            st.caption("The material library and the global color palette editor are available directly below the 3D exploded view.")

    _render_material_library_editor()

    if show_palette_editor:
        st.divider()
        _render_palette_editor()
