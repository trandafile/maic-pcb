import streamlit as st
import os
import json
import urllib.parse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Basic user info scopes
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

def get_secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def init_oauth_flow():
    client_id = get_secret("GOOGLE_CLIENT_ID")
    client_secret = get_secret("GOOGLE_CLIENT_SECRET")
    redirect_uri = get_secret("GOOGLE_REDIRECT_URI", "http://localhost:8501")
    
    if not client_id or not client_secret:
        return None

    client_config = {
        "web": {
            "client_id": client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

def login_button():
    client_id = get_secret("GOOGLE_CLIENT_ID")
    redirect_uri = get_secret("GOOGLE_REDIRECT_URI", "http://localhost:8501")

    if not client_id:
        st.warning("⚠️ Google OAuth credentials not found in secrets.")
        return

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'prompt': 'consent',
        'access_type': 'online',
    }
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
    
    # Using official st.link_button as in maic-tasks
    st.link_button("🔑 Accedi con Google", auth_url, type="primary")

def handle_oauth_callback():
    if 'code' in st.query_params:
        code = st.query_params['code']
        # Clear original query params to prevent re-triggering logic
        st.query_params.clear()
        
        flow = init_oauth_flow()
        if not flow: return
        
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            user_info_service = build('oauth2', 'v2', credentials=creds)
            user_info = user_info_service.userinfo().get().execute()
            
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = user_info.get('email')
            st.session_state['user_name'] = user_info.get('name')
            
            st.rerun()
             
        except Exception as e:
             st.error(f"Login failed (callback): {e}")

def check_login():
    """Checks if user is logged in. Returns True if yes, blocks execution and returns False if not."""
    if st.session_state.get('logged_in', False):
        return True
        
    st.title("PCB Stack-up & Via Visualizer")
    st.markdown("⚠️ **Authentication Required**  \n"
                "To access your centralized Material Library, you must sign in with your Google account.")
    
    handle_oauth_callback()
    
    if not st.session_state.get('logged_in', False):
        login_button()
        
    return False

def logout():
    """Logs the user out by clearing session keys."""
    keys_to_clear = ['logged_in', 'user_email', 'user_name', 'material_library']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
