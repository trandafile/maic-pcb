import streamlit as st

def check_login():
    """Checks if user is logged in using native st.login. Returns True if yes, blocks execution and returns False if not."""
    if st.user.is_logged_in:
        return True
        
    st.title("PCB Stack-up & Via Visualizer")
    st.markdown("⚠️ **Authentication Required**  \n"
                "To access your centralized Material Library, you must sign in with your Google account.")
    
    if st.button("🔑 Sign in with Google", type="primary"):
        st.login("google")
        
    return False

def logout():
    """Logs the user out using native st.logout and clears relevant session state."""
    keys_to_clear = ['material_library']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.logout()
