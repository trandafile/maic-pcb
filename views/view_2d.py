import streamlit as st
import streamlit.components.v1 as components
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

    # Plotly 2D Cross-Section View
    st.subheader("Plotly Cross-Section")
    fig = plotly_engine_2d.build_2d_figure(stackup_data, show_id=show_id, show_name=show_name)
    st.plotly_chart(fig, use_container_width=True, height=600)

    st.divider()
    
    # HTML/CSS Engine View
    st.subheader("HTML/CSS Horizontal Bar View")
    palette = st.selectbox("🎨 CSS Render Palette:", ["classic", "cool_technical", "realistic"], index=0)
    html_out = html_engine_2d.render_html(stackup_data, palette=palette, show_id=show_id, show_name=show_name)
    components.html(html_out, height=800, scrolling=True)

    st.divider()
    from core import svg_engine_2d
    svg_str = svg_engine_2d.render_svg(stackup_data, palette=palette)
    st.download_button("💾 Export 2D Vector (SVG)", data=svg_str, file_name="board_stackup_2d.svg", mime="image/svg+xml", type="primary")

    with st.expander("Debug: Current Stack-up Dictionary"):
        st.json(stackup_data)
