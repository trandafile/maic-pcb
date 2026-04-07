import plotly.graph_objects as go


def format_layer_label(layer, show_id=True, show_name=True):
    """Format a layer label using the requested `Layer name - ID` ordering."""
    layer_id = str(layer.get('id', '')).strip()
    layer_name = str(layer.get('name', '')).strip()

    parts = []
    if show_name and layer_name:
        parts.append(layer_name)
    if show_id and layer_id:
        parts.append(layer_id)

    if parts:
        return " - ".join(parts)
    return " - ".join(part for part in [layer_name, layer_id] if part) or "Layer"


def calculate_z_map(layers):
    """
    Calculate the top and bottom Y coordinates (depth) for each layer.
    """
    z_map = {}
    current_y = 0.0
    for idx, layer in enumerate(layers):
        y_top = current_y
        y_bottom = current_y - layer.get('thickness', 0)
        z_map[layer['id']] = {
            'index': idx,
            'y_top': y_top,
            'y_bottom': y_bottom,
            'thickness': layer.get('thickness', 0)
        }
        current_y = y_bottom
    return z_map

def get_intersection(layer_idx, via, layer_idx_shape_map):
    """
    Determine how the via intersects the given layer.
    Returns: 'connected', 'unconnected', or None
    """
    if via['start_layer'] not in layer_idx_shape_map or via['end_layer'] not in layer_idx_shape_map:
        return None
        
    idx1 = layer_idx_shape_map[via['start_layer']]
    idx2 = layer_idx_shape_map[via['end_layer']]
    
    start_idx = min(idx1, idx2)
    end_idx = max(idx1, idx2)
    
    if layer_idx == start_idx or layer_idx == end_idx:
        return 'connected'
    elif start_idx < layer_idx < end_idx:
        return 'unconnected'
    else:
        return None

def build_2d_figure(stackup_data, show_id=True, show_name=True):
    """
    Constructs the Plotly 2D Cross-section view.
    Y-axis represents layout depth. X-axis dynamically spaces out the Vias.
    """
    layers = stackup_data.get('layers', [])
    vias = stackup_data.get('vias', [])
    
    z_map = calculate_z_map(layers)
    lid_idx_map = {lid: z['index'] for lid, z in z_map.items()}
    
    # Calculate intelligent X-spacing for vias based on their maximum requested diameters
    # so they never touch.
    via_x_positions = []
    current_x = 0.0
    for via in vias:
        drill_r = float(via.get('drill_diameter', 0.3)) / 2.0
        pad_r = float(via.get('pad_diameter', 0.0)) / 2.0
        antipad_r = float(via.get('antipad_diameter', 0.8)) / 2.0
        
        max_r = max(drill_r, pad_r, antipad_r)
        
        # Add left buffer
        current_x += max_r + 2.0  
        via_x_positions.append(current_x)
        # Add right buffer
        current_x += max_r
        
    x_min = -2.0
    x_max = current_x + 2.0 if vias else 10.0
    
    fig = go.Figure()
    
    # --- 1. DRAW LAYERS ---
    for idx, layer in enumerate(layers):
        lid = layer['id']
        z_info = z_map[lid]
        y_top = z_info['y_top']
        y_bottom = z_info['y_bottom']
        
        # Calculate horizontal segments (Antipads gap)
        antipad_x_gaps = []
        if layer['type'] == 'metal':
            for v_idx, via in enumerate(vias):
                x_pos = via_x_positions[v_idx]
                intersect_type = get_intersection(idx, via, lid_idx_map)
                
                if intersect_type == 'unconnected':
                    ap = float(via.get('antipad_diameter', 0.8))
                    antipad_x_gaps.append((x_pos - ap/2.0, x_pos + ap/2.0))
        
        antipad_x_gaps.sort(key=lambda x: x[0])
        
        merged_gaps = []
        for gap in antipad_x_gaps:
            if not merged_gaps:
                merged_gaps.append(gap)
            else:
                prev = merged_gaps[-1]
                if gap[0] <= prev[1]:
                    merged_gaps[-1] = (prev[0], max(prev[1], gap[1]))
                else:
                    merged_gaps.append(gap)
                    
        segments = []
        current_pos = x_min
        for gap in merged_gaps:
            if gap[0] > current_pos:
                segments.append((current_pos, gap[0]))
            current_pos = gap[1]
        
        if current_pos < x_max:
            segments.append((current_pos, x_max))
            
        color = layer.get('color_hex') 
        if not color:
             color = '#D67D3E' if layer['type'] == 'metal' else '#708090'
             
        opacity = 1.0 if layer['type'] == 'metal' else 0.85
        
        for seg in segments:
            fig.add_shape(
                type="rect",
                x0=seg[0], x1=seg[1], y0=y_bottom, y1=y_top,
                fillcolor=color,
                line=dict(color="#333333", width=1),
                layer="below", 
                opacity=opacity
            )
            
        hover_label = format_layer_label(layer, show_id=True, show_name=True)
        visible_label = format_layer_label(layer, show_id=show_id, show_name=show_name)

        fig.add_trace(go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[y_bottom, y_bottom, y_top, y_top, y_bottom],
            fill="toself",
            fillcolor=color,
            opacity=0.0,
            hoverinfo="text",
            text=f"<b>{hover_label}</b> ({layer['type']})<br>Thick: {z_info['thickness']}mm",
            showlegend=False
        ))

        # Annotations: left label column + right thickness column
        label_y = y_top - (z_info['thickness'] / 2.0)
        thickness_text = f"{float(z_info['thickness']):.3f} mm"

        if visible_label:
            fig.add_annotation(
                x=0.14,
                y=label_y,
                xref="paper",
                yref="y",
                text=visible_label,
                showarrow=False,
                xanchor="right",
                align="right",
                font=dict(size=13, color="#222222")
            )

        fig.add_annotation(
            x=0.92,
            y=label_y,
            xref="paper",
            yref="y",
            text=thickness_text,
            showarrow=False,
            xanchor="left",
            align="left",
            font=dict(size=13, color="#222222")
        )
            
    # --- 2. DRAW VIAS ---
    for v_idx, via in enumerate(vias):
        x_pos = via_x_positions[v_idx]
        
        if via['start_layer'] not in z_map or via['end_layer'] not in z_map:
            continue
            
        via_y_top = z_map[via['start_layer']]['y_top']
        via_y_bottom = z_map[via['end_layer']]['y_bottom']
        
        true_top_y = max(via_y_top, via_y_bottom)
        true_bot_y = min(via_y_top, via_y_bottom)
        
        drill_r = float(via.get('drill_diameter', 0.3)) / 2.0
        plating = float(via.get('plating_thickness', 0.025))
        
        wall_color = "#B87333" 
        
        # Left wall
        fig.add_shape(
            type="rect",
            x0=x_pos - drill_r, x1=x_pos - drill_r + plating,
            y0=true_bot_y, y1=true_top_y,
            fillcolor=wall_color,
            line_width=1, line_color="#333", layer="above"
        )
        # Right wall
        fig.add_shape(
            type="rect",
            x0=x_pos + drill_r - plating, x1=x_pos + drill_r,
            y0=true_bot_y, y1=true_top_y,
            fillcolor=wall_color,
            line_width=1, line_color="#333", layer="above"
        )
        
        fill_type = via.get('fill_type', 'empty')
        inner_color = "white" if fill_type == "empty" else ("#B87333" if fill_type=="copper_plated" else "#333333")
        inner_opacity = 0.0 if fill_type == "empty" else 0.8
        
        if plating < drill_r and fill_type != "empty":
            fig.add_shape(
                type="rect",
                x0=x_pos - drill_r + plating, x1=x_pos + drill_r - plating,
                y0=true_bot_y, y1=true_top_y,
                fillcolor=inner_color,
                line_width=0, layer="above",
                opacity=inner_opacity
            )
            
        fig.add_trace(go.Scatter(
            x=[x_pos],
            y=[true_bot_y + (true_top_y - true_bot_y)/2],
            mode="markers",
            marker=dict(size=float(via.get('drill_diameter', 0.3))*40, opacity=0),
            hoverinfo="text",
            text=f"<b>Via: {via['id']}</b><br>Drill: {via.get('drill_diameter',0)}mm",
            showlegend=False
        ))

        if show_id or show_name:
            fig.add_annotation(
                x=x_pos,
                y=true_top_y + (abs(true_top_y)*0.02 + 0.1),
                text=f"{via['id']}",
                showarrow=False,
                textangle=0,
                xanchor="center",
                yanchor="bottom"
            )

    fig.update_xaxes(showgrid=False, zeroline=False, visible=False, range=[x_min - 2, x_max + 2])
    # Remove horizontal thickness grid lines as requested
    fig.update_yaxes(showgrid=False, zeroline=False, title="Thickness (mm)", tickformat=".3f")
    fig.update_layout(
        plot_bgcolor='#FAFAFA',
        paper_bgcolor="#FFFFFF",
        margin=dict(l=190, r=150, t=60, b=40),
        height=650,
        showlegend=False,
        hovermode="closest"
    )
    
    return fig
