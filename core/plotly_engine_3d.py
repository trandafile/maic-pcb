import plotly.graph_objects as go
import numpy as np

def build_3d_figure(stackup_data, explosion_factor):
    """
    Renders the PCB Stack-up as a 3D Plotly Graph Object models.
    """
    fig = go.Figure()
    
    layers = stackup_data.get('layers', [])
    vias = stackup_data.get('vias', [])
    
    # Base configuration for building the 3D visual blocks
    current_z = 0.0
    layer_z_coords = {}
    width = 10.0
    length = 10.0
    
    for i, layer in enumerate(layers):
        thickness = float(layer.get('thickness', 0.1))
        l_type = layer.get('type', 'dielectric')
        
        # Explosion logic: Shift layer down by i * explosion_factor
        z_offset = current_z - (i * explosion_factor)
        z_top = z_offset
        z_bottom = z_offset - thickness
        
        layer_z_coords[layer['id']] = {"z_top": z_top, "z_bottom": z_bottom}
        
        # Determine Color Map
        if l_type == 'metal' or l_type == 'copper':
            color = layer.get('color_hex') or '#CC5500' # Strict Orange Palette
            opacity = 1.0 # Opaque metal
        else:
            color = layer.get('color_hex') or '#708090' # Strict Matte Earth Tones
            opacity = 0.25 # Highly transparent dielectric to see vias
            
        # Draw Mesh3d Layer Block
        x = [0, width, width, 0,  0, width, width, 0]
        y = [0, 0, length, length,  0, 0, length, length]
        z = [z_top, z_top, z_top, z_top, z_bottom, z_bottom, z_bottom, z_bottom]
        
        i_tris = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        j_tris = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        k_tris = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        
        fig.add_trace(go.Mesh3d(
            x=x, y=y, z=z,
            i=i_tris, j=j_tris, k=k_tris,
            color=color,
            opacity=opacity,
            name=f"[{layer['id']}] {layer.get('name', 'Layer')}",
            hoverinfo="name",
            flatshading=True
        ))
        
        current_z -= thickness
        
    # Draw Vias
    # Using cylinders (Mesh3d) is graphically heavier than Scatter3d.
    # To represent realistic 3D tubes, we map circles to Mesh3d.
    for i, via in enumerate(vias):
        s_layer = via.get('start_layer')
        e_layer = via.get('end_layer')
        drill = float(via.get('drill_diameter', 0.3))
        
        if s_layer in layer_z_coords and e_layer in layer_z_coords:
            z_top = layer_z_coords[s_layer]['z_top']
            z_bottom = layer_z_coords[e_layer]['z_bottom']
            
            # Place vias uniformly along the X axis
            vx = 2.0 + (i * 1.5)
            if vx > width - 1: vx = width / 2.0
            
            # Math to generate cylinder points
            theta = np.linspace(0, 2*np.pi, 20)
            z_grid = np.linspace(z_bottom, z_top, 2)
            theta_grid, z_grid = np.meshgrid(theta, z_grid)
            r = drill / 2.0
            x_grid = vx + r * np.cos(theta_grid)
            y_grid = (length / 2) + r * np.sin(theta_grid)
            
            fig.add_trace(go.Surface(
                x=x_grid, y=y_grid, z=z_grid,
                colorscale=[[0, '#B87333'], [1, '#B87333']], # Copper plating
                showscale=False,
                opacity=1.0,
                name=via.get('id', 'Via'),
                hoverinfo="name"
            ))
            
    # Polishing Layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, range=[-1, width+1]),
            yaxis=dict(visible=False, range=[-1, length+1]),
            zaxis=dict(title='', showgrid=False, zeroline=False, showticklabels=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=-1.5, z=0.5)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        title="3D Exploded Representation",
        showlegend=False
    )
    
    return fig
