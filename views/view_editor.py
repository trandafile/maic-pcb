import ast
import re

import pandas as pd
import streamlit as st

from core import color_manager, hfss_exporter, via_utils
from core.layer_utils import is_metal_layer

# Spec section 4.2 via fields with the same defaults the renderers fall back to
# (plotly_engine_2d / svg_engine_2d). Keeping them editable here means the user
# intent survives the JSON roundtrip instead of being silently dropped.
VIA_FIELD_DEFAULTS = {
    "drill_diameter": 0.3,
    "pad_diameter": 0.0,
    "antipad_diameter": 0.8,
    "plating_thickness": 0.025,
    "fill_type": "empty",
    "label": "",
}
# Back-drill (spec 4.3): optional, defaults keep pre-existing projects unchanged.
VIA_FIELD_DEFAULTS.update(via_utils.BACKDRILL_FIELD_DEFAULTS)
VIA_BACKDRILL_NUMERIC_FIELDS = ("backdrill_diameter", "backdrill_stub")
VIA_FILL_TYPES = ["empty", "epoxy", "copper_plated"]
VIA_COLUMN_ORDER = ["id", "type", "start_layer", "end_layer"] + list(VIA_FIELD_DEFAULTS)


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
    role = color_manager.get_default_palette_role(layer_type)
    return color_manager.get_role_color(st.session_state, role)


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


def _get_color_presets():
    return color_manager.build_preset_options(st.session_state)


def _find_best_color_preset_index(presets, defaults, final_type):
    preferred_role = defaults.get("palette_role") or color_manager.get_default_palette_role(defaults.get("type") or final_type)
    for idx, preset in enumerate(presets):
        if preset["role"] == preferred_role:
            return idx

    current_color = _normalize_hex_color(defaults.get("color_hex"), presets[0]["hex"])
    for idx, preset in enumerate(presets):
        if _normalize_hex_color(preset["hex"], presets[0]["hex"]) == current_color:
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
                min_value=0.001,
                value=max(float(defaults.get("thickness", 0.0) or 0.0), 0.001),
                step=0.01,
                format="%.3f",
                key=f"{key_prefix}_thickness_manual",
                help="Zero-thickness layers would collapse the Z-coordinate calculation.",
            )

    final_type = _resolve_layer_type(cat_gui, selected_row or {})

    current_color = _normalize_hex_color(
        defaults.get("color_hex"),
        _default_color_for_type(final_type),
    )
    color_presets = _get_color_presets()
    preset_labels = [preset["label"] for preset in color_presets]
    preset_map = {preset["label"]: preset for preset in color_presets}
    preset_index = _find_best_color_preset_index(color_presets, defaults, final_type)

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
            help="Choose a numbered palette color. Layers linked to `Col#1`...`Col#4` will follow the active palette.",
        )
        selected_preset = preset_map[selected_preset_label]
        preset_color = selected_preset["hex"]

    with c7:
        use_custom_color = st.toggle(
            "Use custom color / hex",
            value=defaults.get("color_source") == "custom",
            key=f"{key_prefix}_use_custom_color",
            help="Enable a free color picker with editable hex value. Custom colors remain unchanged when the global palette changes.",
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
        "color_source": "custom" if use_custom_color else "palette",
        "palette_role": selected_preset["role"],
    }


def _vias_referencing_layer(layer_id):
    """Vias that use the given layer as start or end (spec section 5)."""
    return [
        via for via in st.session_state['stackup_data'].get('vias', [])
        if via.get('start_layer') == layer_id or via.get('end_layer') == layer_id
    ]


def _sanitize_backdrill(via, via_id, layers, layer_index, errors, warnings):
    """Normalize and validate the optional back-drill fields of a single via.

    A back-drill shortens the barrel: the stop layer is the LAST layer that
    must stay CONNECTED, so it has to sit strictly inside the via span on the
    drilled side (see `core/via_utils.py`)."""
    side = str(via.get('backdrill_side', 'none') or 'none').strip().lower()
    if side not in via_utils.BACKDRILL_SIDES:
        side = 'none'
    via['backdrill_side'] = side

    for field in VIA_BACKDRILL_NUMERIC_FIELDS:
        try:
            via[field] = float(via.get(field, VIA_FIELD_DEFAULTS[field]))
        except (TypeError, ValueError):
            via[field] = VIA_FIELD_DEFAULTS[field]
    via['backdrill_diameter'] = max(0.0, via['backdrill_diameter'])
    via['backdrill_stub'] = max(0.0, via['backdrill_stub'])

    via['backdrill_top_layer'] = str(via.get('backdrill_top_layer') or "").strip()
    via['backdrill_bottom_layer'] = str(via.get('backdrill_bottom_layer') or "").strip()

    if side == 'none':
        return

    top_idx = min(layer_index[via['start_layer']], layer_index[via['end_layer']])
    bot_idx = max(layer_index[via['start_layer']], layer_index[via['end_layer']])

    if via['backdrill_diameter'] > 0.0 and via['backdrill_diameter'] <= via['drill_diameter']:
        errors.append(
            f"Via '{via_id}': back-drill diameter ({via['backdrill_diameter']:.3f} mm) must be larger "
            f"than the drill diameter ({via['drill_diameter']:.3f} mm). Use 0 for automatic sizing."
        )

    stop_indices = {}
    checks = []
    if side in ('top', 'both'):
        checks.append(('top', 'backdrill_top_layer', "below the start layer"))
    if side in ('bottom', 'both'):
        checks.append(('bottom', 'backdrill_bottom_layer', "above the end layer"))

    for which, field, hint in checks:
        stop_id = via[field]
        if not stop_id:
            errors.append(f"Via '{via_id}': back-drill from {which} needs a stop layer.")
            continue
        if stop_id not in layer_index:
            errors.append(f"Via '{via_id}': back-drill stop layer '{stop_id}' does not exist.")
            continue

        stop_idx = layer_index[stop_id]
        valid = (top_idx < stop_idx <= bot_idx) if which == 'top' else (top_idx <= stop_idx < bot_idx)
        if not valid:
            errors.append(
                f"Via '{via_id}': back-drill stop layer '{stop_id}' must be inside the via span and {hint}."
            )
            continue

        stop_indices[which] = stop_idx
        if not is_metal_layer(layers[stop_idx]):
            warnings.append(
                f"Via '{via_id}': back-drill stops on '{stop_id}', which is not a metal layer."
            )

    if 'top' in stop_indices and 'bottom' in stop_indices and stop_indices['top'] > stop_indices['bottom']:
        errors.append(
            f"Via '{via_id}': the two back-drills overlap "
            f"('{via['backdrill_top_layer']}' is below '{via['backdrill_bottom_layer']}')."
        )


def _sanitize_vias(records, layers):
    """Validate the via table before saving: unique non-empty IDs, start/end
    referencing existing layers, numeric fields coerced with renderer-matching
    defaults (NaN cells from the data editor are normalized away), plus the
    optional back-drill definition."""
    cleaned = []
    errors = []
    warnings = []
    seen_ids = set()

    layer_index = {layer.get('id'): idx for idx, layer in enumerate(layers)}
    valid_layer_ids = set(layer_index)

    for row in records:
        via = {key: value for key, value in row.items() if not pd.isna(value)}

        via_id = str(via.get('id') or "").strip()
        if not via_id:
            errors.append("Every via needs a non-empty ID.")
            continue
        if via_id in seen_ids:
            errors.append(f"Duplicate via ID '{via_id}': IDs must be unique.")
            continue
        seen_ids.add(via_id)
        via['id'] = via_id

        start = via.get('start_layer')
        end = via.get('end_layer')
        if start not in valid_layer_ids or end not in valid_layer_ids:
            errors.append(f"Via '{via_id}': start/end must reference existing layer IDs.")
            continue
        if start == end:
            errors.append(f"Via '{via_id}': start and end layer cannot be the same.")
            continue

        for field in ("drill_diameter", "pad_diameter", "antipad_diameter", "plating_thickness"):
            try:
                via[field] = float(via.get(field, VIA_FIELD_DEFAULTS[field]))
            except (TypeError, ValueError):
                via[field] = VIA_FIELD_DEFAULTS[field]

        if via.get('fill_type') not in VIA_FILL_TYPES:
            via['fill_type'] = VIA_FIELD_DEFAULTS['fill_type']
        via.setdefault('label', VIA_FIELD_DEFAULTS['label'])

        _sanitize_backdrill(via, via_id, layers, layer_index, errors, warnings)

        cleaned.append(via)

    return cleaned, errors, warnings


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
        existing_ids = {layer.get('id') for layer in layers}
        if not new_layer["id"]:
            st.error("Layer ID is required.")
        elif new_layer["id"] in existing_ids:
            st.error(f"Layer ID '{new_layer['id']}' already exists: IDs must be unique (vias reference layers by ID).")
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
            other_ids = {layer.get('id') for i, layer in enumerate(layers) if i != selected_idx}
            if not edited_layer["id"]:
                st.error("Layer ID is required.")
            elif edited_layer["id"] in other_ids:
                st.error(f"Layer ID '{edited_layer['id']}' already exists: IDs must be unique (vias reference layers by ID).")
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
                blocking_vias = _vias_referencing_layer(sel_move_id)
                if blocking_vias:
                    via_ids = ", ".join(str(v.get('id', '?')) for v in blocking_vias)
                    st.error(
                        f"Cannot delete layer '{sel_move_id}': it is the start/end layer of via(s) {via_ids}. "
                        "Delete or re-route those vias first (spec section 5)."
                    )
                else:
                    st.session_state['stackup_data']['layers'].pop(idx)
                    st.rerun()

    st.divider()

    # --- 5. VIA EDITOR ---
    st.subheader("3. Interconnect Vias")
    st.markdown("You can define vias by specifying Start and End layers directly.")
    st.caption(
        "🕳️ **Back-drill (optional):** pick the side(s) to drill from and the **stop layer**, i.e. the "
        "last layer that must stay **connected**. The barrel is removed from that surface down to "
        "`BD Stub` mm before the stop layer, shortening the via. "
        "Leave `BD Diameter` at 0 for automatic sizing "
        f"(drill + {via_utils.BACKDRILL_AUTO_OVERSIZE_MM:.2f} mm)."
    )

    vias = st.session_state['stackup_data']['vias']
    df_vias = pd.DataFrame(vias) if vias else pd.DataFrame(columns=VIA_COLUMN_ORDER)

    # Older projects may miss the spec 4.2 fields: surface them with the same
    # defaults the renderers would silently apply, so they become editable.
    for column, default in VIA_FIELD_DEFAULTS.items():
        if column not in df_vias.columns:
            df_vias[column] = default
        else:
            df_vias[column] = df_vias[column].fillna(default)
    extra_columns = [c for c in df_vias.columns if c not in VIA_COLUMN_ORDER]
    df_vias = df_vias[VIA_COLUMN_ORDER + extra_columns]

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
            "pad_diameter": st.column_config.NumberColumn("Pad (mm)", min_value=0.0, format="%.3f", help="Pad diameter on connected layers (0 = no pad)."),
            "antipad_diameter": st.column_config.NumberColumn("Antipad (mm)", min_value=0.0, format="%.3f", help="Clearance hole on crossed-but-unconnected metal layers."),
            "plating_thickness": st.column_config.NumberColumn("Plating (mm)", min_value=0.0, format="%.3f", help="Copper thickness on the barrel walls."),
            "fill_type": st.column_config.SelectboxColumn("Fill", options=VIA_FILL_TYPES, help="empty (hollow), epoxy (resin filled), copper_plated (solid copper)."),
            "label": st.column_config.TextColumn("Display Label"),
            "backdrill_side": st.column_config.SelectboxColumn(
                "BD Side",
                options=via_utils.BACKDRILL_SIDES,
                help="Side(s) the back-drill enters from. 'none' disables the back-drill.",
            ),
            "backdrill_top_layer": st.column_config.SelectboxColumn(
                "BD Stop (top)",
                options=[""] + layer_ids,
                help="Drilling from the top: last layer that must stay connected.",
            ),
            "backdrill_bottom_layer": st.column_config.SelectboxColumn(
                "BD Stop (bottom)",
                options=[""] + layer_ids,
                help="Drilling from the bottom: last layer that must stay connected.",
            ),
            "backdrill_diameter": st.column_config.NumberColumn(
                "BD Diameter (mm)",
                min_value=0.0,
                format="%.3f",
                help=f"Back-drill bit diameter, must exceed the drill. 0 = auto (drill + {via_utils.BACKDRILL_AUTO_OVERSIZE_MM:.2f} mm).",
            ),
            "backdrill_stub": st.column_config.NumberColumn(
                "BD Stub (mm)",
                min_value=0.0,
                format="%.3f",
                help="Residual barrel left between the drill end and the stop layer.",
            ),
        },
        key="vias_editor_state",
        width="stretch"
    )

    if st.button("💾 Apply Via Table Settings"):
        cleaned_vias, via_errors, via_warnings = _sanitize_vias(
            edited_df_vias.to_dict('records'),
            layers,
        )
        if via_errors:
            for message in via_errors:
                st.error(message)
        else:
            # Toasts (unlike st.warning) survive the rerun below.
            for message in via_warnings:
                st.toast(f"⚠️ {message}")
            st.session_state['stackup_data']['vias'] = cleaned_vias
            st.toast("✅ Vias Saved!")
            st.rerun()
