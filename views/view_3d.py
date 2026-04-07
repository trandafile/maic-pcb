import streamlit as st
from core.plotly_engine_3d import build_3d_figure
from views import view_library

def render():
    st.subheader("3D Exploded View")
    st.markdown("Use the **3D Explosion Slider** in the sidebar to dynamically separate the layers and inspect the internal via structures.")

    stackup_data = st.session_state.get('stackup_data')
    explosion_factor = st.session_state.get('explosion_factor', 0.0)
    show_id = st.session_state.get('show_id', True)
    show_name = st.session_state.get('show_name', True)

    if not stackup_data or not stackup_data.get('layers'):
        st.warning("No stack-up data available. Build your layers in the Stack-up Editor first.")
        return

    with st.spinner("Rendering 3D Mesh..."):
        fig = build_3d_figure(
            stackup_data,
            explosion_factor,
            show_id=show_id,
            show_name=show_name,
        )
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
            st.warning(
                f"SVG export is unavailable in this environment because Plotly static export requires `kaleido==0.2.1`. Details: {e}"
            )

    st.divider()
    view_library.render(show_title=False, show_palette_editor=True, embedded=True)
