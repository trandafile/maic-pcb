import os
import ast
from core import color_manager

def layer_height_px(thickness_um: float, layer_type: str) -> int:
    """
    Converts real thickness to pixel height for rendering using compressed log scale.
    """
    if layer_type == "copper":
        if thickness_um <= 18: return 10
        elif thickness_um <= 35: return 14
        elif thickness_um <= 70: return 18
        else: return 22
    else:
        # Dielectric or other
        if thickness_um <= 100:
            return 14 + int((thickness_um - 50) * 0.2)
        elif thickness_um <= 400:
            return 24 + int((thickness_um - 100) * 0.08)
        else:
            return 48 + int((thickness_um - 400) * 0.02)

def generate_css(palette_name="Classic", palette_colors=None):
    """
    Returns the core CSS for the visual engine using the shared global palette.
    """
    render_palette = color_manager.build_render_palette(palette_name, palette_colors)
    palettes_css = f"""
    .stackup-viewer {{
        --cu-top: {render_palette['cu_top']}; --cu-bot: {render_palette['cu_bot']}; --cu-text: {render_palette['cu_text']};
        --pp-top: {render_palette['pp_top']}; --pp-bot: {render_palette['pp_bot']}; --pp-text: {render_palette['pp_text']};
        --core-top: {render_palette['core_top']}; --core-bot: {render_palette['core_bot']}; --core-text: {render_palette['core_text']};
        --sm-top: {render_palette['sm_top']}; --sm-bot: {render_palette['sm_bot']}; --sm-text: {render_palette['sm_text']};
        --ss-top: {render_palette['ss_top']}; --ss-bot: {render_palette['ss_bot']}; --ss-text: {render_palette['ss_text']};

        --via-l: {render_palette['via_l']}; --via-c: {render_palette['via_c']}; --via-r: {render_palette['via_r']};
        --via-pad-t: {render_palette['via_pad_t']}; --via-pad-b: {render_palette['via_pad_b']};
        --via-hole: {render_palette['via_hole']};

        font-family: 'Inter', 'Segoe UI', sans-serif;
        background: #F9FAFB;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        min-width: 600px;
    }}

    .stackup-header {{ margin-bottom: 20px; font-weight: bold; font-size: 1.2rem; color: #333; }}
    .stackup-body {{ position: relative; width: 100%; display: flex; flex-direction: column; }}
    
    .layer-row {{
        display: flex;
        align-items: center;
        width: 100%;
        position: relative;
    }}
    
    .layer-label {{
        width: 170px; text-align: right; padding-right: 15px; font-size: 11px; font-weight: bold; z-index: 2;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }}
    .layer-bar {{ flex: 1; min-width: 300px; height: 100%; position: relative; display: flex; align-items: center; justify-content: flex-start; padding-left: 16px; font-size: 11px; z-index: 1;}}
    /* Material text lives LEFT of the via corridor and never runs under it. */
    .layer-bar .mat-text {{
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        line-height: 1; pointer-events: none;
    }}
    .layer-dim {{ width: 70px; text-align: left; padding-left: 15px; font-size: 11px; font-family: monospace; color: #666; z-index: 2;}}
    
    /* Layer Gradients */
    .layer-bar.copper {{ background: linear-gradient(180deg, var(--cu-top) 0%, var(--cu-bot) 100%); color: var(--cu-text); border-top: 1px solid rgba(0,0,0,0.1); border-bottom: 1px solid rgba(0,0,0,0.1); }}
    .layer-label.copper {{ color: var(--cu-top); }}
    
    .layer-bar.prepreg {{ background: linear-gradient(180deg, var(--pp-top) 0%, var(--pp-bot) 100%); color: var(--pp-text); }}
    .layer-label.prepreg {{ color: var(--pp-bot); }}
    
    .layer-bar.core {{ background: linear-gradient(180deg, var(--core-top) 0%, var(--core-bot) 100%); color: var(--core-text); }}
    .layer-label.core {{ color: var(--core-bot); }}
    
    .layer-bar.soldermask {{ background: linear-gradient(180deg, var(--sm-top) 0%, var(--sm-bot) 100%); color: var(--sm-text); }}
    .layer-bar.silkscreen {{ background: linear-gradient(180deg, var(--ss-top) 0%, var(--ss-bot) 100%); color: var(--ss-text); border: 1px dashed #ccc;}}
    
    /* Vias */
    .via-zone {{
        position: absolute;
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 10;
    }}
    
    .via-barrel {{
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, var(--via-l) 0%, var(--via-c) 50%, var(--via-r) 100%);
        position: absolute;
    }}
    
    .via-hole {{
        width: 40%;
        height: 100%;
        background: var(--via-hole);
        position: absolute;
    }}
    
    .via-pad {{
        position: absolute;
        width: 140%;
        height: 4px;
        background: linear-gradient(90deg, var(--via-pad-t) 0%, var(--via-pad-b) 100%);
        box-shadow: 0 1px 2px rgba(0,0,0,0.3);
        border-radius: 1px;
    }}
    
    .via-pad.top {{ top: -2px; }}
    .via-pad.bot {{ bottom: -2px; }}
    
    .uvia-barrel {{
        clip-path: polygon(25% 0, 75% 0, 100% 100%, 0 100%);
    }}
    
    .via-label {{
        position: absolute;
        bottom: -25px;
        font-size: 10px;
        color: #444;
        text-align: center;
        white-space: nowrap;
        font-weight: bold;
    }}

    /* Via labels rotate 45 deg so they never overlap, regardless of how many
       vias are present or how long their names are. Anchored at the via
       center; a leader tick connects label to barrel. */
    .via-bottom-label {{
        position: absolute;
        font-size: 10px;
        color: #444;
        white-space: nowrap;
        font-weight: bold;
        z-index: 11;
        transform: rotate(45deg);
        transform-origin: top left;
    }}

    .via-leader {{
        position: absolute;
        width: 1px;
        background: #999;
        z-index: 10;
    }}

    .via-label-row {{
        position: relative;
        width: 100%;
        margin-top: 2px;
    }}
    """
    
    # Optional dynamic injections
    css = palettes_css.replace('var(--cu-top)', 'var(--cu-top)')
    return css

def _css_type(layer) -> str:
    """Map the layer 'type' (mixed vocabulary) to the CSS class family."""
    l_type = str(layer.get('type', 'core')).lower()
    if "copper" in l_type or "metal" in l_type: return "copper"
    if "prepreg" in l_type: return "prepreg"
    if "core" in l_type: return "core"
    if "solder" in l_type: return "soldermask"
    if "silk" in l_type: return "silkscreen"
    return "core"


def _label_row_height(stackup_data, show_id=True, show_name=True) -> int:
    """Height (px) of the rotated via-label band, from the longest label."""
    layers = stackup_data.get('layers', [])
    vias = stackup_data.get('vias', [])
    id_set = {l.get('id') for l in layers}
    labels = [
        _format_via_label(v, show_id=show_id, show_name=show_name)
        for v in vias
        if v.get('start_layer') in id_set and v.get('end_layer') in id_set
    ]
    max_chars = max((len(t) for t in labels), default=0)
    if max_chars == 0:
        return 0
    return min(220, max(44, int(max_chars * 6.0 * 0.71) + 24))


def estimate_height(stackup_data, show_id=True, show_name=True) -> int:
    """Pixel height the rendered HTML needs (for the Streamlit iframe)."""
    layers = stackup_data.get('layers', [])
    stack_px = sum(
        layer_height_px(float(l.get('thickness', 0.0)) * 1000.0, _css_type(l))
        for l in layers
    )
    chrome_px = 150  # viewer padding + header + body padding
    return stack_px + _label_row_height(stackup_data, show_id, show_name) + chrome_px


def _format_layer_label(layer, show_id=True, show_name=True):
    """Format a layer label using `Layer name - ID` when both toggles are enabled."""
    layer_id = str(layer.get('id', '')).strip()
    layer_name = str(layer.get('name', '')).strip()

    parts = []
    if show_name and layer_name:
        parts.append(layer_name)
    if show_id and layer_id:
        parts.append(layer_id)

    if parts:
        return " - ".join(parts)
    return " - ".join(part for part in [layer_name, layer_id] if part) or "&nbsp;"


def _format_via_label(via, show_id=True, show_name=True):
    """Format a via label using `Via name - ID` when both toggles are enabled."""
    via_id = str(via.get('id', '')).strip()
    via_name = str(via.get('name', '')).strip()
    if not via_name:
        via_name = str(via.get('label', '')).strip()
    via_name = via_name.replace("\n", " ")

    show_name_part = show_name and bool(via_name)
    show_id_part = show_id and bool(via_id)

    # Single line: the labels are rendered rotated 45 deg under the vias.
    if show_name_part and show_id_part:
        return f"{via_name} — {via_id}"
    if show_name_part:
        return via_name
    if show_id_part:
        return via_id
    return ""


def render_html(stackup_data, palette="Classic", show_id=True, show_name=True, palette_colors=None):
    """
    Generates the complete HTML string for the PCB visual engine.
    """
    layers = stackup_data.get('layers', [])
    vias = stackup_data.get('vias', [])

    total_thickness = sum([float(l.get('thickness', 0)) for l in layers])

    # --- Geometry of the via corridor (computed BEFORE emitting any row) ---
    # Material text occupies the left part of the bar; vias get a dedicated
    # corridor to its right, so the two can never overlap whatever the count.
    bar_left = 185            # layer-label width (170) + its padding (15)
    via_x_start = 330         # corridor start, relative to the layer bar
    via_spacing = 48          # horizontal pitch between vias (rotated labels)
    mat_text_max = via_x_start - 40

    id_set = {l.get('id') for l in layers}
    drawable_vias = [
        v for v in vias
        if v.get('start_layer') in id_set and v.get('end_layer') in id_set
    ]
    n_vias = len(drawable_vias)
    corridor_end = via_x_start + n_vias * via_spacing if n_vias else via_x_start
    bar_min_width = corridor_end + 80

    # Rotated 45-deg labels: height of the label band scales with the longest
    # label (chars * char_width * sin45), clamped to a sane range.
    label_row_height = _label_row_height(stackup_data, show_id, show_name)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>{generate_css(palette, palette_colors)}</style>
        <style>.layer-bar {{ min-width: {bar_min_width}px; }}</style>
    </head>
    <body>
    <div class="stackup-viewer" data-palette="{palette}">
        <div class="stackup-header">
            <span class="stackup-title">Custom Stack-up Configuration — {total_thickness:.3f}mm</span>
        </div>
        <div class="stackup-body" style="padding: 0px 0 20px 0;">
    """
    
    # Pre-calculate absolute Y offsets for layers to position vias properly
    layer_map = []
    current_y = 0
    
    # 1. GENERATE LAYER ROWS
    for idx, layer in enumerate(layers):
        name = layer.get('name', f"L{idx}")
        thick_mm = float(layer.get('thickness', 0.0))
        thick_um = thick_mm * 1000.0

        css_type = _css_type(layer)

        px_h = layer_height_px(thick_um, css_type)
        
        layer_map.append({
            "idx": idx,
            "id": layer.get('id', str(idx)),
            "y_top": current_y,
            "y_bot": current_y + px_h,
            "px_h": px_h,
            "type": css_type
        })
        
        current_y += px_h

        label_text = _format_layer_label(layer, show_id=show_id, show_name=show_name)
        material_ref = str(layer.get('material_ref', '') or '')
        bar_tooltip = f"{name} — {material_ref} — {thick_mm:.3f} mm"
        # Thin bars (e.g. 35 um copper) cannot host readable text: keep the
        # bar clean and leave the full info in the tooltip.
        mat_html = (
            f'<span class="mat-text" style="max-width:{mat_text_max}px">{material_ref}</span>'
            if px_h >= 13 else ''
        )

        html += f"""
            <div class="layer-row" style="height:{px_h}px">
                <div class="layer-label {css_type}" title="{label_text}">{label_text}</div>
                <div class="layer-bar {css_type}" title="{bar_tooltip}">{mat_html}</div>
                <div class="layer-dim">{thick_mm:.3f} mm</div>
            </div>
        """
        
    id_to_idx = {m['id']: m['idx'] for m in layer_map}
        
    # 2. GENERATE VIAS — drawn in the dedicated corridor right of the
    # material text; labels rotated 45 deg below, with a thin leader tick.
    stack_bottom_y = current_y
    via_x_px = via_x_start
    via_labels_html = ""

    for via in drawable_vias:
        s_id = via.get('start_layer')
        e_id = via.get('end_layer')
        v_type = via.get('type', 'PTH').upper()
        drill_um = float(via.get('drill_diameter', 0.15)) * 1000.0
        label_text = _format_via_label(via, show_id=show_id, show_name=show_name)

        s_idx = id_to_idx[s_id]
        e_idx = id_to_idx[e_id]

        top_idx = min(s_idx, e_idx)
        bot_idx = max(s_idx, e_idx)

        top_y = layer_map[top_idx]['y_top']
        bot_y = layer_map[bot_idx]['y_bot']

        via_height = bot_y - top_y

        # Dimension scaling
        v_width = max(8, min(24, drill_um / 15)) # Proportional mapping px length

        extra_css_class = "uvia-barrel" if v_type == "UVIA" else ""

        # Determine Pad Visibility (Loop through intersected layers)
        pads_html = ""
        for l_idx in range(top_idx, bot_idx + 1):
            lyr = layer_map[l_idx]
            if lyr['type'] == 'copper':
                if l_idx == top_idx:
                    pad_y = -2.0 # Top edge of via (top layer)
                elif l_idx == bot_idx:
                    pad_y = via_height - 2.0 # Bottom edge of via (bottom layer)
                else:
                    pad_y = lyr['y_top'] - top_y - 2.0 # Top edge of intersection for internal pads

                pads_html += f'<div class="via-pad" style="top:{pad_y}px"></div>\n                '

        html += f"""
            <div class="via-zone" title="{label_text}" style="left:calc({bar_left}px + {via_x_px}px); top:{top_y}px; height:{via_height}px; width:{v_width}px;">
                <div class="via-barrel {extra_css_class}"></div>
                <div class="via-hole" style="height:100%"></div>
                {pads_html}
            </div>
            """

        if label_text:
            label_center_x = via_x_px + (v_width / 2.0)
            # Leader tick from the via barrel down into the label band.
            leader_h = stack_bottom_y - bot_y + 10
            via_labels_html += (
                f'<div class="via-leader" style="left:calc({bar_left}px + {label_center_x}px); '
                f'top:-{leader_h}px; height:{leader_h + 4}px;"></div>'
                f'<div class="via-bottom-label" style="left:calc({bar_left}px + {label_center_x}px); '
                f'top:8px;">{label_text}</div>'
            )

        via_x_px += via_spacing

    if via_labels_html:
        html += f"""
        <div class="via-label-row" style="height:{label_row_height}px">
            {via_labels_html}
        </div>
        """
            
    html += """
        </div>
    </div>
    </body>
    </html>
    """
    return html
