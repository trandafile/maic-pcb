import streamlit as st
import streamlit.components.v1 as components
from core import color_manager
from core import html_engine_2d
from core import plotly_engine_2d

def render():
    """
    Renders the 2D visualization views.
    """
    st.subheader("2D PCB Stack-up View")

    # Extract data from state
    stackup_data = st.session_state.get('stackup_data', {})
    
    # Get toggle states
    show_id = st.session_state.get('show_id', True)
    show_name = st.session_state.get('show_name', True)

    color_manager.ensure_palette_state(st.session_state)
    palette_name = color_manager.get_active_palette_name(st.session_state)
    palette_colors = color_manager.get_active_palette_colors(st.session_state)

    # Plotly 2D Cross-Section View
    st.subheader("Plotly Cross-Section")
    fig = plotly_engine_2d.build_2d_figure(stackup_data, show_id=show_id, show_name=show_name)
    st.plotly_chart(fig, use_container_width=True, height=600)

    st.divider()

    # HTML/CSS Engine View
    st.subheader("HTML/CSS Horizontal Bar View")
    st.caption(f"🎨 Active palette: **{palette_name}**")
    html_out = html_engine_2d.render_html(
        stackup_data,
        palette=palette_name,
        show_id=show_id,
        show_name=show_name,
        palette_colors=palette_colors,
    )
    components.html(html_out, height=800, scrolling=True)

    st.divider()
    from core import svg_engine_2d
    svg_str = svg_engine_2d.render_svg(stackup_data, palette=palette_name, palette_colors=palette_colors)
    st.download_button("💾 Export 2D Vector (SVG)", data=svg_str, file_name="board_stackup_2d.svg", mime="image/svg+xml", type="primary")

    with st.expander("Debug: Current Stack-up Dictionary"):
        st.json(stackup_data)
