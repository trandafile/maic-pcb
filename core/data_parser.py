import pandas as pd
import gspread
import streamlit as st
import os
import json
from google.oauth2.credentials import Credentials

SHEET_ID = "1gX-RaYRxpPgClUkKnBqvoUVKW3cZBaheQpYvh1uFoKA"

@st.cache_data(ttl=600, show_spinner="Connecting to Centralized Database...")
def get_cloud_library_via_service_account():
    """
    Downloads the sheet using the fixed bot credentials (Service Account).
    """
    try:
        # 1. Use the Service Account credentials
        client = gspread.service_account(filename='credenziali-bot.json')
        doc = client.open_by_key(SHEET_ID)
        sheet = doc.sheet1
        data = sheet.get_all_records()
        if data:
            return pd.DataFrame(data)
    except Exception as e:
        # Show exact bot email for easier troubleshooting
        bot_email = "bot-hipa-privato@hipa-489107.iam.gserviceaccount.com"
        st.error(f"🚨 **Material Database Access Error**  \n"
                 f"The app could not connect to the Google Sheet.  \n"
                 f"Please ensure you have shared the sheet with the following email:  \n"
                 f"`{bot_email}`  \n"
                 f"Error detail: {e}")
        return None

def get_gspread_client():
    """Returns a gspread client using Secrets (Cloud) or local JSON (Dev)."""
    # 1. Search for Service Account credentials in st.secrets (any case)
    creds_json = None
    for key in ["GOOGLE_SERVICE_ACCOUNT_JSON", "google_service_account_json", "SERVICE_ACCOUNT"]:
        if key in st.secrets:
            creds_json = st.secrets[key]
            break
            
    if creds_json:
        try:
            import json
            service_acc_info = json.loads(creds_json) if isinstance(creds_json, str) else dict(creds_json)
            return gspread.service_account_from_dict(service_acc_info)
        except Exception as e:
            st.error(f"🚨 Invalid credentials in Secrets: {e}")
            
    # 2. Try to load from local file (for Local Development only)
    if os.path.exists('credenziali-bot.json'):
        try:
            return gspread.service_account(filename='credenziali-bot.json')
        except Exception as e:
            st.error(f"🚨 Local credentials error: {e}")
            
    # If still here, we failed. Raise a helpful exception.
    raise FileNotFoundError("Google Credentials NOT found. Please add 'GOOGLE_SERVICE_ACCOUNT_JSON' to your Streamlit Cloud Secrets.")

def get_cloud_library_via_service_account():
    """Fetches full library using the service account helper."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        sheet = doc.sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"🚨 Library Fetch Error: {e}")
        return None

def get_material_library():
    """
    Returns the Material Library exclusively from Google Sheets.
    No local Excel fallback or Mock data permitted.
    """
    df = get_cloud_library_via_service_account()
    
    if df is not None:
        return df
    
    # If we reached here, loading failed. Return empty DF to block logical errors.
    return pd.DataFrame()
def save_stackup_to_cloud(project_name, stackup_data):
    """Saves or updates a project state in the 'SavedProjects' tab."""
    try:
        import datetime
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        
        try:
            ws = doc.worksheet("SavedProjects")
        except gspread.WorksheetNotFound:
            ws = doc.add_worksheet(title="SavedProjects", rows="100", cols="5")
            ws.append_row(["Timestamp", "ProjectName", "Project_JSON"])
            
        all_data = ws.get_all_values()
        project_json = json.dumps(stackup_data)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if project exists for Update vs Append
        found_idx = -1
        for i, row in enumerate(all_data):
            if i > 0 and len(row) > 1 and row[1] == project_name:
                found_idx = i + 1 
                break
        
        if found_idx > 0:
            ws.update(range_name=f'A{found_idx}:C{found_idx}', values=[[timestamp, project_name, project_json]])
        else:
            ws.append_row([timestamp, project_name, project_json])
        return True
    except Exception as e:
        st.error(f"🚨 Cloud Save Error: {e}")
        return False

def get_project_list():
    """Returns a list of saved project names from the Cloud."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        ws = doc.worksheet("SavedProjects")
        data = ws.get_all_values()
        return [row[1] for i, row in enumerate(data) if i > 0]
    except:
        return []

def load_project_from_cloud(project_name):
    """Loads a specific project by name."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        ws = doc.worksheet("SavedProjects")
        data = ws.get_all_values()
        for i, row in enumerate(data):
            if i > 0 and row[1] == project_name:
                return json.loads(row[2])
    except Exception as e:
        st.error(f"🚨 Cloud Load Error: {e}")
    return None

def delete_project_from_cloud(project_name):
    """Removes a project row from the Cloud."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        ws = doc.worksheet("SavedProjects")
        data = ws.get_all_values()
        for i, row in enumerate(data):
            if i > 0 and row[1] == project_name:
                ws.delete_rows(i + 1)
                return True
    except Exception as e:
        st.error(f"🚨 Cloud Delete Error: {e}")
    return False

def save_material_library_to_cloud(df):
    """Overwrites the main material library sheet with current session state."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        sheet = doc.sheet1
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"🚨 Library Sync Error: {e}")
        return False
