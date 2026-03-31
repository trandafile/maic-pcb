from core.html_engine_2d import layer_height_px

# Define identical SVG color mappings
PALETTES = {
    "classic": {
        "cu_top": "#E8923A", "cu_bot": "#C06820", "cu_text": "#4A2810",
        "pp_top": "#A8BC80", "pp_bot": "#7A9050", "pp_text": "#3A4828",
        "core_top": "#8BA060", "core_bot": "#5A7030", "core_text": "#C8E0A0",
        "sm_top": "#2E8B57", "sm_bot": "#006400", "sm_text": "#E0FFE0",
        "ss_top": "#FFFFFF", "ss_bot": "#E0E0E0", "ss_text": "#000000",
        "via_l": "#A85A20", "via_c": "#D4782C", "via_r": "#A85A20",
        "via_pad_t": "#F0A048", "via_pad_b": "#D88030", "via_hole": "#1a1a1a"
    },
    "cool_technical": {
        "cu_top": "#64B5F6", "cu_bot": "#1976D2", "cu_text": "#0D47A1",
        "pp_top": "#E0E0E0", "pp_bot": "#BDBDBD", "pp_text": "#616161",
        "core_top": "#90A4AE", "core_bot": "#607D8B", "core_text": "#ECEFF1",
        "sm_top": "#2E8B57", "sm_bot": "#006400", "sm_text": "#E0FFE0",
        "ss_top": "#FFFFFF", "ss_bot": "#E0E0E0", "ss_text": "#000000",
        "via_l": "#1565C0", "via_c": "#42A5F5", "via_r": "#1565C0",
        "via_pad_t": "#64B5F6", "via_pad_b": "#1E88E5", "via_hole": "#1a1a1a"
    },
    "realistic": {
        "cu_top": "#D4A574", "cu_bot": "#B8860B", "cu_text": "#8B4513",
        "pp_top": "#F5F5DC", "pp_bot": "#D4C896", "pp_text": "#8B8B00",
        "core_top": "#BDB76B", "core_bot": "#8B8B00", "core_text": "#FFFFF0",
        "sm_top": "#2E8B57", "sm_bot": "#006400", "sm_text": "#E0FFE0",
        "ss_top": "#FFFFFF", "ss_bot": "#E0E0E0", "ss_text": "#000000",
        "via_l": "#8B4513", "via_c": "#D4A574", "via_r": "#8B4513",
        "via_pad_t": "#E6C88A", "via_pad_b": "#CD853F", "via_hole": "#1a1a1a"
    }
}

def render_svg(stackup_data, palette="classic"):
    p = PALETTES.get(palette, PALETTES["classic"])
    
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
        # Left Label
        svg += f'<text x="{x_offset - 10}" y="{l["y_top"] + (l["px_h"]/2) + 4}" fill="{t_col}" font-size="12px" font-weight="bold" text-anchor="end">{l["name"]}</text>\n'
        # Right Thickness
        svg += f'<text x="{x_offset + rect_width + 10}" y="{l["y_top"] + (l["px_h"]/2) + 4}" fill="#666" font-size="11px" font-family="monospace">{l["thick_mm"]:.3f} mm</text>\n'
        # Center Material label (approx)
        svg += f'<text x="{x_offset + rect_width/2}" y="{l["y_top"] + (l["px_h"]/2) + 4}" fill="{t_col}" font-size="11px" text-anchor="middle">{l["material"]}</text>\n'
        
    # 2. Vias
    via_x_px = x_offset + 50
    via_spacing = 60
    id_to_idx = {m['id']: m['idx'] for m in layer_map}
    
    for via in vias:
        s_idx = id_to_idx.get(via.get('start_layer'))
        e_idx = id_to_idx.get(via.get('end_layer'))
        
        if s_idx is not None and e_idx is not None:
            top_idx = min(s_idx, e_idx)
            bot_idx = max(s_idx, e_idx)
            
            top_y = layer_map[top_idx]['y_top']
            bot_y = layer_map[bot_idx]['y_bot']
            via_h = bot_y - top_y
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
            
            # Pads
            pad_w = v_width * 1.4
            pad_x = via_x_px + (v_width - pad_w) / 2
            
            for l_idx in range(top_idx, bot_idx + 1):
                lyr = layer_map[l_idx]
                if lyr['type'] == 'copper':
                    if l_idx == top_idx: pad_y = top_y - 2.0
                    elif l_idx == bot_idx: pad_y = bot_y - 2.0
                    else: pad_y = lyr['y_top'] - 2.0
                    
                    svg += f'<rect x="{pad_x}" y="{pad_y}" width="{pad_w}" height="4" fill="url(#grad-via-pad)" rx="1"/>\n'
                    
            # Label
            lbl = f"{v_type} {layer_map[top_idx]['id']}-{layer_map[bot_idx]['id']}"
            svg += f'<text x="{via_x_px + v_width/2}" y="{bot_y + 15}" fill="#444" font-size="10px" font-weight="bold" text-anchor="middle">{lbl}</text>\n'
            
            via_x_px += via_spacing
            
    svg += "</svg>"
    return svg
