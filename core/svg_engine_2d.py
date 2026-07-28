from core import color_manager
from core import via_utils
from core.html_engine_2d import layer_height_px, _format_layer_label, _backdrill_width_px


def render_svg(stackup_data, palette="Classic", palette_colors=None):
    p = color_manager.build_render_palette(palette, palette_colors)
    
    layers = stackup_data.get('layers', [])
    vias = stackup_data.get('vias', [])
    
    layer_map = []
    current_y = 40 # Top padding
    
    # Pre-calculate layer bounds
    for idx, layer in enumerate(layers):
        l_type = layer.get('type', 'core').lower()
        thick_mm = float(layer.get('thickness', 0.0))
        thick_um = thick_mm * 1000.0
        
        css_type = l_type
        if "copper" in l_type or "metal" in l_type: css_type = "copper"
        elif "prepreg" in l_type: css_type = "prepreg"
        elif "core" in l_type: css_type = "core"
        elif "solder" in l_type: css_type = "soldermask"
        elif "silk" in l_type: css_type = "silkscreen"
        else: css_type = "core"
        
        px_h = layer_height_px(thick_um, css_type)
        
        layer_map.append({
            "idx": idx,
            "id": layer.get('id', str(idx)),
            "name": layer.get('name', f"L{idx}"),
            "material": layer.get('material_ref', ''),
            "thick_mm": thick_mm,
            "y_top": current_y,
            "y_bot": current_y + px_h,
            "px_h": px_h,
            "type": css_type
        })
        current_y += px_h
        
    total_height = current_y + 80
    svg_width = 800
    x_offset = 120
    rect_width = svg_width - 240
    
    # Gradient Defs
    defs = f"""<defs>
        <linearGradient id="grad-copper" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{p['cu_top']}"/><stop offset="100%" stop-color="{p['cu_bot']}"/></linearGradient>
        <linearGradient id="grad-prepreg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{p['pp_top']}"/><stop offset="100%" stop-color="{p['pp_bot']}"/></linearGradient>
        <linearGradient id="grad-core" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{p['core_top']}"/><stop offset="100%" stop-color="{p['core_bot']}"/></linearGradient>
        <linearGradient id="grad-soldermask" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{p['sm_top']}"/><stop offset="100%" stop-color="{p['sm_bot']}"/></linearGradient>
        <linearGradient id="grad-silkscreen" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{p['ss_top']}"/><stop offset="100%" stop-color="{p['ss_bot']}"/></linearGradient>
        <linearGradient id="grad-via-barrel" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{p['via_l']}"/><stop offset="50%" stop-color="{p['via_c']}"/><stop offset="100%" stop-color="{p['via_r']}"/></linearGradient>
        <linearGradient id="grad-via-pad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{p['via_pad_t']}"/><stop offset="100%" stop-color="{p['via_pad_b']}"/></linearGradient>
    </defs>"""
    
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {total_height}" width="100%" height="100%" style="background-color:#F9FAFB; font-family:sans-serif;">\n{defs}\n'
    
    # 1. Base Layer Rects & Text
    for l in layer_map:
        t_col = p.get(f"{l['type']}_text", "#000")
        svg += f'<rect x="{x_offset}" y="{l["y_top"]}" width="{rect_width}" height="{l["px_h"]}" fill="url(#grad-{l["type"]})" stroke="rgba(0,0,0,0.1)" stroke-width="1"/>\n'
        label_text = _format_layer_label({"id": l["id"], "name": l["name"]}, show_id=True, show_name=True)
        svg += f'<text x="{x_offset - 10}" y="{l["y_top"] + (l["px_h"]/2) + 4}" fill="{t_col}" font-size="12px" font-weight="bold" text-anchor="end">{label_text}</text>\n'
        # Right Thickness
        svg += f'<text x="{x_offset + rect_width + 10}" y="{l["y_top"] + (l["px_h"]/2) + 4}" fill="#666" font-size="11px" font-family="monospace">{l["thick_mm"]:.3f} mm</text>\n'
        # Center Material label (approx)
        svg += f'<text x="{x_offset + rect_width/2}" y="{l["y_top"] + (l["px_h"]/2) + 4}" fill="{t_col}" font-size="11px" text-anchor="middle">{l["material"]}</text>\n'
        
    # 2. Vias
    via_x_px = x_offset + 50
    via_spacing = 60
    id_to_idx = {m['id']: m['idx'] for m in layer_map}
    layer_ids = [m['id'] for m in layer_map]

    for via in vias:
        geom = via_utils.resolve(via, id_to_idx)

        if geom is not None:
            top_idx = geom['top_idx']
            bot_idx = geom['bot_idx']

            # Nominal (as-drilled) extent, before any back-drill.
            nominal_top_y = layer_map[top_idx]['y_top']
            nominal_bot_y = layer_map[bot_idx]['y_bot']

            # Live extent: the back-drill removes the stub, stopping
            # BACKDRILL_STUB_PX short of the stop layer that stays connected.
            live_top_idx = geom['eff_top_idx']
            live_bot_idx = geom['eff_bot_idx']
            top_y = nominal_top_y
            bot_y = nominal_bot_y
            if geom['bd_top_idx'] is not None:
                top_y = max(nominal_top_y, layer_map[live_top_idx]['y_top'] - via_utils.BACKDRILL_STUB_PX)
            if geom['bd_bot_idx'] is not None:
                bot_y = min(nominal_bot_y, layer_map[live_bot_idx]['y_bot'] + via_utils.BACKDRILL_STUB_PX)

            via_h = max(1.0, bot_y - top_y)
            drill_um = float(via.get('drill_diameter', 0.15)) * 1000.0
            v_width = max(8.0, min(24.0, drill_um / 15.0))

            # Barrel
            v_type = via.get('type', 'PTH').upper()
            if v_type == "UVIA":
                # Conical polygon (clip-path equivalent)
                p1 = f"{via_x_px + v_width*0.25},{top_y}"
                p2 = f"{via_x_px + v_width*0.75},{top_y}"
                p3 = f"{via_x_px + v_width},{bot_y}"
                p4 = f"{via_x_px},{bot_y}"
                svg += f'<polygon points="{p1} {p2} {p3} {p4}" fill="url(#grad-via-barrel)"/>\n'
            else:
                svg += f'<rect x="{via_x_px}" y="{top_y}" width="{v_width}" height="{via_h}" fill="url(#grad-via-barrel)"/>\n'

            # Hole
            hole_w = v_width * 0.4
            hole_x = via_x_px + (v_width - hole_w) / 2
            if v_type == "UVIA":
                p1 = f"{hole_x + hole_w*0.25},{top_y}"
                p2 = f"{hole_x + hole_w*0.75},{top_y}"
                p3 = f"{hole_x + hole_w},{bot_y}"
                p4 = f"{hole_x},{bot_y}"
                svg += f'<polygon points="{p1} {p2} {p3} {p4}" fill="{p["via_hole"]}"/>\n'
            else:
                svg += f'<rect x="{hole_x}" y="{top_y}" width="{hole_w}" height="{via_h}" fill="{p["via_hole"]}"/>\n'

            # Pads: only on the layers the live barrel still reaches.
            pad_w = v_width * 1.4
            pad_x = via_x_px + (v_width - pad_w) / 2

            for l_idx in range(live_top_idx, live_bot_idx + 1):
                lyr = layer_map[l_idx]
                if lyr['type'] == 'copper':
                    if l_idx == live_bot_idx: pad_y = lyr['y_bot'] - 2.0
                    else: pad_y = lyr['y_top'] - 2.0

                    svg += f'<rect x="{pad_x}" y="{pad_y}" width="{pad_w}" height="4" fill="url(#grad-via-pad)" rx="1"/>\n'

            # Back-drill bore(s): the removed sections, hollow + dashed outline.
            if geom['has_backdrill']:
                bd_w = _backdrill_width_px(v_width, via, geom)
                bd_x = via_x_px + (v_width - bd_w) / 2.0
                removed_spans = []
                if top_y > nominal_top_y:
                    removed_spans.append((nominal_top_y, top_y))
                if bot_y < nominal_bot_y:
                    removed_spans.append((bot_y, nominal_bot_y))

                for span_top, span_bot in removed_spans:
                    svg += (
                        f'<rect x="{bd_x:.1f}" y="{span_top:.1f}" width="{bd_w:.1f}" '
                        f'height="{max(1.0, span_bot - span_top):.1f}" fill="#FFFFFF" fill-opacity="0.88" '
                        f'stroke="#8A8A8A" stroke-width="1" stroke-dasharray="3 2"/>\n'
                    )

            # Label
            lbl = f"{v_type} {layer_map[top_idx]['id']}-{layer_map[bot_idx]['id']}"
            svg += f'<text x="{via_x_px + v_width/2}" y="{nominal_bot_y + 15}" fill="#444" font-size="10px" font-weight="bold" text-anchor="middle">{lbl}</text>\n'

            if geom['has_backdrill']:
                bd_parts = []
                if geom['bd_top_idx'] is not None:
                    bd_parts.append(f"T&#8594;{layer_ids[geom['bd_top_idx']]}")
                if geom['bd_bot_idx'] is not None:
                    bd_parts.append(f"B&#8594;{layer_ids[geom['bd_bot_idx']]}")
                bd_lbl = "BD " + " ".join(bd_parts)
                svg += f'<text x="{via_x_px + v_width/2}" y="{nominal_bot_y + 26}" fill="#777" font-size="9px" text-anchor="middle">{bd_lbl}</text>\n'

            via_x_px += via_spacing

    svg += "</svg>"
    return svg
