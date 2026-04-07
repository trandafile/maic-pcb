import ast
import re

import pandas as pd
import streamlit as st

from core import hfss_exporter


def _normalize_text(value):
    return str(value or "").strip().lower()


def _infer_gui_category(layer):
    layer_type = _normalize_text(layer.get("type"))
    combined = " ".join(
        [
            layer_type,
            _normalize_text(layer.get("name")),
            _normalize_text(layer.get("material_ref")),
        ]
    )

    if "copper" in combined or layer_type == "metal":
        return "metal layer"
    if any(token in combined for token in ["core", "prepreg", "dielectric"]):
        return "dielectric substrate"
    return "cover"


def _allowed_categories_for_gui(cat_gui):
    if cat_gui == "dielectric substrate":
        return {"core", "prepreg"}
    if cat_gui == "metal layer":
        return {"copper", "copper foil"}
    return {"soldermask", "solder mask", "silkscreen", "silk screen", "cover"}


def _filter_material_library(df_lib, cat_gui):
    if df_lib.empty or "Category" not in df_lib.columns:
        return pd.DataFrame()

    df_filtered = df_lib.copy()
    df_filtered["_normalized_category"] = df_filtered["Category"].apply(_normalize_text)
    allowed = _allowed_categories_for_gui(cat_gui)
    df_filtered = df_filtered[df_filtered["_normalized_category"].isin(allowed)]
    return df_filtered.drop(columns=["_normalized_category"], errors="ignore")


def _build_material_options(filtered_df):
    options = []
    option_map = {}

    if filtered_df.empty:
        return options, option_map

    for _, row in filtered_df.iterrows():
        label = f"{row.get('Brand', '')} ➔ {row.get('Type/Code', '')} [{row.get('Category', '')}]"
        options.append(label)
        option_map[label] = row.to_dict()

    return options, option_map


def _parse_thicknesses(raw_value):
    if raw_value is None or raw_value == "":
        return []

    parsed = raw_value
    if isinstance(raw_value, str):
        try:
            parsed = ast.literal_eval(raw_value)
        except Exception:
            return []

    if isinstance(parsed, (list, tuple)):
        return [float(value) for value in parsed]

    return []


def _default_color_for_type(layer_type):
    if layer_type == "copper":
        return "#CC5500"
    if layer_type in {"soldermask", "cover"}:
        return "#2E8B57"
    return "#708090"


def _normalize_hex_color(value, fallback):
    color = str(value or "").strip()
    if not color:
        color = fallback

    if not color.startswith("#"):
        color = f"#{color}"

    if re.fullmatch(r"#[0-9a-fA-F]{3}", color):
        color = "#" + "".join(ch * 2 for ch in color[1:])

    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        color = fallback

    return color.upper()


def _get_color_presets(layer_type):
    if layer_type == "copper":
        return [
            ("Copper Orange", "#CC5500"),
            ("Coral Copper", "#FF7F50"),
            ("Bronze", "#B87333"),
            ("Amber", "#D67D3E"),
        ]

    if layer_type in {"core", "prepreg", "dielectric"}:
        return [
            ("Slate Gray", "#708090"),
            ("Muted Olive", "#556B2F"),
            ("Dust Blue", "#5F7180"),
            ("Moss", "#6B7D5C"),
        ]

    return [
        ("Soldermask Green", "#2E8B57"),
        ("Teal", "#3B7A78"),
        ("Slate Gray", "#708090"),
        ("Muted Olive", "#556B2F"),
    ]


def _find_best_color_preset_index(presets, current_color):
    normalized = _normalize_hex_color(current_color, presets[0][1])
    for idx, (_, hex_value) in enumerate(presets):
        if _normalize_hex_color(hex_value, presets[0][1]) == normalized:
            return idx
    return 0


def _resolve_layer_type(cat_gui, selected_row):
    row_category = _normalize_text(selected_row.get("Category")) if selected_row else ""

    if cat_gui == "metal layer":
        return "copper"
    if cat_gui == "dielectric substrate":
        return row_category if row_category in {"core", "prepreg"} else "core"
    return "soldermask"


def _find_best_material_index(options, current_value):
    if not options:
        return None

    current_value = str(current_value or "")
    for idx, option in enumerate(options):
        if option == current_value:
            return idx

    for idx, option in enumerate(options):
        if current_value and current_value in option:
            return idx

    return 0


def _find_best_thickness_index(options, current_value):
    if not options:
        return None

    try:
        current_value = float(current_value)
    except (TypeError, ValueError):
        return 0

    for idx, option in enumerate(options):
        if abs(float(option) - current_value) < 1e-9:
            return idx

    return 0


def _render_layer_inputs(df_lib, defaults, key_prefix, id_default):
    cat_default = _infer_gui_category(defaults)
    cat_options = ["dielectric substrate", "metal layer", "cover"]
    cat_index = cat_options.index(cat_default) if cat_default in cat_options else 0

    c1, c2, c3 = st.columns(3)

    with c1:
        cat_gui = st.selectbox("1. Category", cat_options, index=cat_index, key=f"{key_prefix}_category")

    filtered_df = _filter_material_library(df_lib, cat_gui)
    mat_options, option_map = _build_material_options(filtered_df)

    selected_row = None
    if mat_options:
        default_mat_index = _find_best_material_index(mat_options, defaults.get("material_ref"))
        with c2:
            selected_mat_str = st.selectbox(
                "2. Material Type/Code",
                mat_options,
                index=default_mat_index,
                key=f"{key_prefix}_material",
            )
        selected_row = option_map.get(selected_mat_str)
    else:
        with c2:
            selected_mat_str = st.text_input(
                "2. Material Type/Code",
                value=str(defaults.get("material_ref", "")),
                key=f"{key_prefix}_material_text",
            )

    thickness_opts = _parse_thicknesses(selected_row.get("Available_Thicknesses")) if selected_row else []

    with c3:
        if thickness_opts:
            thickness_index = _find_best_thickness_index(thickness_opts, defaults.get("thickness", 0.0))
            thickness_val = st.selectbox(
                "3. Allowed Thickness (mm)",
                thickness_opts,
                index=thickness_index,
                key=f"{key_prefix}_thickness",
            )
        else:
            thickness_val = st.number_input(
                "3. Thickness (mm)",
                min_value=0.0,
                value=float(defaults.get("thickness", 0.0) or 0.0),
                step=0.01,
                format="%.3f",
                key=f"{key_prefix}_thickness_manual",
            )

    final_type = _resolve_layer_type(cat_gui, selected_row or {})

    current_color = _normalize_hex_color(
        defaults.get("color_hex"),
        _default_color_for_type(final_type),
    )
    color_presets = _get_color_presets(final_type)
    preset_labels = [f"{name} ({hex_value})" for name, hex_value in color_presets]
    preset_map = dict(zip(preset_labels, [hex_value for _, hex_value in color_presets]))
    preset_index = _find_best_color_preset_index(color_presets, current_color)

    c4, c5 = st.columns(2)
    with c4:
        layer_id = st.text_input(
            "Layer ID (e.g. L1, D1)",
            value=str(defaults.get("id") or id_default),
            key=f"{key_prefix}_id",
        )
    with c5:
        layer_name = st.text_input(
            "Layer Name (Label)",
            value=str(defaults.get("name") or "New Layer"),
            key=f"{key_prefix}_name",
        )

    c6, c7 = st.columns([1.2, 1])
    with c6:
        selected_preset_label = st.selectbox(
            "Preset Color",
            preset_labels,
            index=preset_index,
            key=f"{key_prefix}_color_preset",
            help="Choose from the recommended technical palette.",
        )
        preset_color = preset_map[selected_preset_label]

    with c7:
        use_custom_color = st.toggle(
            "Use custom color / hex",
            value=current_color not in preset_map.values(),
            key=f"{key_prefix}_use_custom_color",
            help="Enable a free color picker with editable hex value.",
        )
        color_hex = st.color_picker(
            "Custom Color",
            value=current_color if use_custom_color else preset_color,
            key=f"{key_prefix}_color_picker",
            disabled=not use_custom_color,
        )

    final_color = _normalize_hex_color(
        color_hex if use_custom_color else preset_color,
        _default_color_for_type(final_type),
    )

    return {
        "id": layer_id.strip(),
        "name": layer_name.strip(),
        "type": final_type,
        "thickness": float(thickness_val),
        "material_ref": selected_mat_str,
        "color_hex": final_color,
    }


def _update_via_layer_references(old_id, new_id):
    if old_id == new_id:
        return

    for via in st.session_state['stackup_data'].get('vias', []):
        if via.get('start_layer') == old_id:
            via['start_layer'] = new_id
        if via.get('end_layer') == old_id:
            via['end_layer'] = new_id


def render():
    st.title("Stack-up Editor & Constructor")
    st.markdown("Manage the current PCB stack-up, add new layers, edit existing ones, and export the HFSS build script.")

    # --- 1. CURRENT STACK-UP VIEW ---
    st.subheader("1. Current PCB Layers")

    layers = st.session_state['stackup_data']['layers']
    df_layers = pd.DataFrame(layers)

    df_lib = st.session_state.get('material_library', pd.DataFrame())
    if not df_lib.empty:
        st.caption("🌐 Material Database Source: **Google Cloud (Live via Service Account)**")
    else:
        st.warning("Material library unavailable: manual layer editing is still enabled.")

    if not df_layers.empty:
        st.dataframe(df_layers, width="stretch", hide_index=True)
    else:
        st.info("No layers in stack-up yet.")

    st.divider()

    # --- 2. ADD / EDIT LAYER FORM ---
    st.subheader("🛠️ Add New / Edit Layer")

    st.markdown("### ➕ Add New Layer")
    st.caption("Add new layers using the current Category ➔ Material ➔ Thickness flow.")
    new_layer = _render_layer_inputs(
        df_lib=df_lib,
        defaults={},
        key_prefix="add_layer",
        id_default=f"L{len(layers) + 1}",
    )

    if st.button("➕ Push Layer to Stack-up", type="primary", width="stretch", key="add_layer_button"):
        if not new_layer["id"]:
            st.error("Layer ID is required.")
        else:
            st.session_state['stackup_data']['layers'].insert(0, new_layer)
            st.toast(f"✅ Layer {new_layer['id']} added on top of stack")
            st.rerun()

    st.markdown("### ✏️ Edit Existing Layer")
    if not layers:
        st.info("Add at least one layer before editing.")
    else:
        selected_layer_id = st.selectbox(
            "Select Layer ID",
            [layer['id'] for layer in layers],
            key="edit_layer_selector",
        )
        selected_idx = next((i for i, layer in enumerate(layers) if layer['id'] == selected_layer_id), 0)
        selected_layer = layers[selected_idx]
        edit_key_prefix = f"edit_layer_{selected_layer.get('id', selected_idx)}"

        st.caption(f"Editing layer: `[{selected_layer.get('id', '?')}] {selected_layer.get('name', 'Unnamed Layer')}`")

        edited_layer = _render_layer_inputs(
            df_lib=df_lib,
            defaults=selected_layer,
            key_prefix=edit_key_prefix,
            id_default=selected_layer.get("id", f"L{selected_idx + 1}"),
        )

        if st.button("💾 Update Selected Layer", type="primary", width="stretch", key="edit_layer_button"):
            if not edited_layer["id"]:
                st.error("Layer ID is required.")
            else:
                original_id = selected_layer.get("id")
                st.session_state['stackup_data']['layers'][selected_idx] = edited_layer
                _update_via_layer_references(original_id, edited_layer["id"])
                st.toast(f"✅ Layer {edited_layer['id']} updated")
                st.rerun()

    st.divider()

    # --- 3. HFSS EXPORT ---
    st.subheader("📜 HFSS Export")
    st.caption("Exports a Python AEDT script with `Z=0` at the base of the lowest dielectric and copper Z variables computed from the stack-up rules.")
    hfss_script = hfss_exporter.generate_hfss_script(st.session_state['stackup_data'])
    st.download_button(
        "Export HFSS Script",
        data=hfss_script,
        file_name="pcb_stackup_hfss.py",
        mime="text/x-python",
        width="stretch",
    )

    st.divider()

    # --- 4. REORDER AND DELETE ---
    st.subheader("↔️ Reorder & Remove")
    if len(layers) > 0:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sel_move_id = st.selectbox("Select Layer to affect:", [l['id'] for l in layers], key="sel_move")
        with c2:
            st.write("")
            idx = next((i for i, l in enumerate(layers) if l['id'] == sel_move_id), -1)
            if st.button("⬆️ Move Up", disabled=idx <= 0, width="stretch"):
                layers[idx - 1], layers[idx] = layers[idx], layers[idx - 1]
                st.session_state['stackup_data']['layers'] = layers
                st.rerun()
        with c3:
            st.write("")
            if st.button("⬇️ Move Down", disabled=idx == len(layers) - 1, width="stretch"):
                layers[idx + 1], layers[idx] = layers[idx], layers[idx + 1]
                st.session_state['stackup_data']['layers'] = layers
                st.rerun()
        with c4:
            st.write("")
            if st.button("🗑️ Delete Form", type="primary", width="stretch"):
                st.session_state['stackup_data']['layers'].pop(idx)
                st.rerun()

    st.divider()

    # --- 5. VIA EDITOR ---
    st.subheader("3. Interconnect Vias")
    st.markdown("You can define vias by specifying Start and End layers directly.")

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
