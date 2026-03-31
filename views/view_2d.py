import streamlit as st
import streamlit.components.v1 as components
from core import html_engine_2d

def render():
    """
    Renders the 2D HTML/CSS Core Engine.
    """
    st.subheader("2D Horizontal Bar View (HTML/CSS Engine)")
    
    # Extract data from state
    stackup_data = st.session_state.get('stackup_data', {})
    
    # Palette Selection
    palette = st.selectbox("🎨 CSS Render Palette:", ["classic", "cool_technical", "realistic"], index=0)
    
    # Build & Render Figure
    html_out = html_engine_2d.render_html(stackup_data, palette=palette)
    
    # Using components.html so the internal CSS isolates perfectly and doesn't collide with app CSS
    components.html(html_out, height=800, scrolling=True)
    
    st.divider()
    from core import svg_engine_2d
    svg_str = svg_engine_2d.render_svg(stackup_data, palette=palette)
    st.download_button("💾 Export 2D Vector (SVG)", data=svg_str, file_name="board_stackup_2d.svg", mime="image/svg+xml", type="primary")
    
    with st.expander("Debug: Current Stack-up Dictionary"):
        st.json(stackup_data)
