import os
import ast

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

def generate_css(palette_name="classic"):
    """
    Returns the core CSS for the visual engine.
    """
    # The palettes 
    palettes_css = """
    .stackup-viewer {
        --cu-top: #E8923A; --cu-bot: #C06820; --cu-text: #4A2810;
        --pp-top: #A8BC80; --pp-bot: #7A9050; --pp-text: #3A4828;
        --core-top: #8BA060; --core-bot: #5A7030; --core-text: #C8E0A0;
        --sm-top: #2E8B57; --sm-bot: #006400; --sm-text: #E0FFE0;
        --ss-top: #FFFFFF; --ss-bot: #E0E0E0; --ss-text: #000000;
        
        --via-l: #A85A20; --via-c: #D4782C; --via-r: #A85A20;
        --via-pad-t: #F0A048; --via-pad-b: #D88030;
        --via-hole: #1a1a1a;
        
        font-family: 'Inter', 'Segoe UI', sans-serif;
        background: #F9FAFB;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        min-width: 600px;
    }
    
    .stackup-viewer[data-palette="cool_technical"] {
        --cu-top: #64B5F6; --cu-bot: #1976D2; --cu-text: #0D47A1;
        --pp-top: #E0E0E0; --pp-bot: #BDBDBD; --pp-text: #616161;
        --core-top: #90A4AE; --core-bot: #607D8B; --core-text: #ECEFF1;
        --via-l: #1565C0; --via-c: #42A5F5; --via-r: #1565C0;
        --via-pad-t: #64B5F6; --via-pad-b: #1E88E5;
    }
    
    .stackup-viewer[data-palette="realistic"] {
        --cu-top: #D4A574; --cu-bot: #B8860B; --cu-text: #8B4513;
        --pp-top: #F5F5DC; --pp-bot: #D4C896; --pp-text: #8B8B00;
        --core-top: #BDB76B; --core-bot: #8B8B00; --core-text: #FFFFF0;
        --via-l: #8B4513; --via-c: #D4A574; --via-r: #8B4513;
        --via-pad-t: #E6C88A; --via-pad-b: #CD853F;
    }

    .stackup-header { margin-bottom: 20px; font-weight: bold; font-size: 1.2rem; color: #333; }
    .stackup-body { position: relative; width: 100%; display: flex; flex-direction: column; }
    
    .layer-row {
        display: flex;
        align-items: center;
        width: 100%;
        position: relative;
    }
    
    .layer-label { width: 120px; text-align: right; padding-right: 15px; font-size: 12px; font-weight: bold; z-index: 2;}
    .layer-bar { flex: 1; min-width: 300px; height: 100%; position: relative; display: flex; align-items: center; justify-content: center; font-size: 11px; z-index: 1;}
    .layer-dim { width: 70px; text-align: left; padding-left: 15px; font-size: 11px; font-family: monospace; color: #666; z-index: 2;}
    
    /* Layer Gradients */
    .layer-bar.copper { background: linear-gradient(180deg, var(--cu-top) 0%, var(--cu-bot) 100%); color: var(--cu-text); border-top: 1px solid rgba(0,0,0,0.1); border-bottom: 1px solid rgba(0,0,0,0.1); }
    .layer-label.copper { color: var(--cu-top); }
    
    .layer-bar.prepreg { background: linear-gradient(180deg, var(--pp-top) 0%, var(--pp-bot) 100%); color: var(--pp-text); }
    .layer-label.prepreg { color: var(--pp-bot); }
    
    .layer-bar.core { background: linear-gradient(180deg, var(--core-top) 0%, var(--core-bot) 100%); color: var(--core-text); }
    .layer-label.core { color: var(--core-bot); }
    
    .layer-bar.soldermask { background: linear-gradient(180deg, var(--sm-top) 0%, var(--sm-bot) 100%); color: var(--sm-text); }
    .layer-bar.silkscreen { background: linear-gradient(180deg, var(--ss-top) 0%, var(--ss-bot) 100%); color: var(--ss-text); border: 1px dashed #ccc;}
    
    /* Vias */
    .via-zone {
        position: absolute;
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 10;
    }
    
    .via-barrel {
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, var(--via-l) 0%, var(--via-c) 50%, var(--via-r) 100%);
        position: absolute;
    }
    
    .via-hole {
        width: 40%;
        height: 100%;
        background: var(--via-hole);
        position: absolute;
    }
    
    .via-pad {
        position: absolute;
        width: 140%;
        height: 4px;
        background: linear-gradient(90deg, var(--via-pad-t) 0%, var(--via-pad-b) 100%);
        box-shadow: 0 1px 2px rgba(0,0,0,0.3);
        border-radius: 1px;
    }
    
    .via-pad.top { top: -2px; }
    .via-pad.bot { bottom: -2px; }
    
    .uvia-barrel {
        clip-path: polygon(25% 0, 75% 0, 100% 100%, 0 100%);
    }
    
    .via-label {
        position: absolute;
        bottom: -25px;
        font-size: 10px;
        color: #444;
        text-align: center;
        white-space: nowrap;
        font-weight: bold;
    }
    """
    
    # Optional dynamic injections
    css = palettes_css.replace('var(--cu-top)', 'var(--cu-top)')
    return css

def render_html(stackup_data, palette="classic"):
    """
    Generates the complete HTML string for the PCB visual engine.
    """
    layers = stackup_data.get('layers', [])
    vias = stackup_data.get('vias', [])
    
    total_thickness = sum([float(l.get('thickness', 0)) for l in layers])
    
    html = f"""
    <html>
    <head>
        <style>{generate_css(palette)}</style>
    </head>
    <body>
    <div class="stackup-viewer" data-palette="{palette}">
        <div class="stackup-header">
            <span class="stackup-title">Custom Stack-up Configuration — {total_thickness:.3f}mm</span>
        </div>
        <div class="stackup-body" style="padding: 0px 0 30px 0;">
    """
    
    # Pre-calculate absolute Y offsets for layers to position vias properly
    layer_map = []
    current_y = 0
    
    # 1. GENERATE LAYER ROWS
    for idx, layer in enumerate(layers):
        l_type = layer.get('type', 'core').lower()
        name = layer.get('name', f"L{idx}")
        thick_mm = float(layer.get('thickness', 0.0))
        thick_um = thick_mm * 1000.0
        
        # Determine CSS class
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
            "y_top": current_y,
            "y_bot": current_y + px_h,
            "px_h": px_h,
            "type": css_type
        })
        
        current_y += px_h
        
        html += f"""
            <div class="layer-row" style="height:{px_h}px">
                <div class="layer-label {css_type}">{name}</div>
                <div class="layer-bar {css_type}">{layer.get('material_ref', '')}</div>
                <div class="layer-dim">{thick_mm:.3f} mm</div>
            </div>
        """
        
    id_to_idx = {m['id']: m['idx'] for m in layer_map}
        
    # 2. GENERATE VIAS
    via_x_px = 150 # Start X position in px relative to layer-bar container
    via_spacing = 60 # px jump between vias
    
    for via in vias:
        s_id = via.get('start_layer')
        e_id = via.get('end_layer')
        v_type = via.get('type', 'PTH').upper()
        drill_um = float(via.get('drill_diameter', 0.15)) * 1000.0
        label = f"{v_type}<br>{s_id} - {e_id}"
        
        s_idx = id_to_idx.get(s_id)
        e_idx = id_to_idx.get(e_id)
        
        if s_idx is not None and e_idx is not None:
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
            <div class="via-zone" style="left:calc(135px + {via_x_px}px); top:{top_y}px; height:{via_height}px; width:{v_width}px;">
                <div class="via-barrel {extra_css_class}"></div>
                <div class="via-hole" style="height:100%"></div>
                {pads_html}
                <div class="via-label">{label}</div>
            </div>
            """
            
            via_x_px += via_spacing
            
    html += """
        </div>
    </div>
    </body>
    </html>
    """
    return html
