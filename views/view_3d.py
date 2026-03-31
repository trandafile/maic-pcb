import streamlit as st
from core.plotly_engine_3d import build_3d_figure

def render():
    st.subheader("3D Exploded View")
    st.markdown("Use the **3D Explosion Slider** in the sidebar to dynamically separate the layers and inspect the internal via structures.")
    
    stackup_data = st.session_state.get('stackup_data')
    explosion_factor = st.session_state.get('explosion_factor', 0.0)
    
    if not stackup_data or not stackup_data.get('layers'):
        st.warning("No stack-up data available. Build your layers in the Stack-up Editor first.")
        return
        
    with st.spinner("Rendering 3D Mesh..."):
        fig = build_3d_figure(stackup_data, explosion_factor)
        st.plotly_chart(fig, width="stretch", height=700)
        
        st.divider()
        try:
            svg_bytes = fig.to_image(format="svg")
            st.download_button(
                label="💾 Export 3D Vector (SVG)", 
                data=svg_bytes, 
                file_name="stackup_3d.svg", 
                mime="image/svg+xml",
                type="primary"
            )
        except Exception as e:
            st.warning("SVG Export is unavailable. Please ensure `kaleido==0.2.1` is installed via pip.")
