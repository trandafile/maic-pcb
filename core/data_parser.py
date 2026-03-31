import pandas as pd
import gspread
import streamlit as st
import os
import json
from google.oauth2.credentials import Credentials

SHEET_ID = "1gX-RaYRxpPgClUkKnBqvoUVKW3cZBaheQpYvh1uFoKA"
MATERIAL_SHEET = "MaterialLibrary"
PROJECT_SHEET = "SavedProjects"

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

def get_or_create_worksheet(doc, title, rows="100", cols="20"):
    """Helper to get a worksheet or create it if not found."""
    try:
        return doc.worksheet(title)
    except gspread.WorksheetNotFound:
        return doc.add_worksheet(title=title, rows=rows, cols=cols)

def get_cloud_library_via_service_account():
    """Fetches full library using the dedicated MaterialLibrary tab."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        
        # Fallback logic: check MaterialLibrary, else try sheet1 to migrate
        try:
            ws = doc.worksheet(MATERIAL_SHEET)
        except gspread.WorksheetNotFound:
            ws = doc.sheet1 # Temporary fallback for first load
            
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"🚨 Library Fetch Error: {e}")
        return None

def get_material_library():
    """Returns the Material Library exclusively from Google Sheets."""
    df = get_cloud_library_via_service_account()
    if df is not None:
        return df
    return pd.DataFrame()

def save_stackup_to_cloud(project_name, stackup_data):
    """Saves or updates a project state in the dedicated 'SavedProjects' tab."""
    try:
        import datetime
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        
        ws = get_or_create_worksheet(doc, PROJECT_SHEET, rows="1000", cols="5")
        all_data = ws.get_all_values()
        
        if not all_data: # If new sheet, add headers
            ws.append_row(["Timestamp", "ProjectName", "Project_JSON"])
            all_data = [["Timestamp", "ProjectName", "Project_JSON"]]
            
        # Clean data: Replace NaN values with None for JSON compliance
        def clean_nans(obj):
            if isinstance(obj, float) and pd.isna(obj):
                return None
            elif isinstance(obj, dict):
                return {k: clean_nans(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nans(v) for v in obj]
            return obj
            
        clean_stackup = clean_nans(stackup_data)
        project_json = json.dumps(clean_stackup)
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
        ws = get_or_create_worksheet(doc, PROJECT_SHEET)
        data = ws.get_all_values()
        return [row[1] for i, row in enumerate(data) if i > 0]
    except:
        return []

def load_project_from_cloud(project_name):
    """Loads a specific project by name from the PROJECTS tab."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        ws = get_or_create_worksheet(doc, PROJECT_SHEET)
        data = ws.get_all_values()
        for i, row in enumerate(data):
            if i > 0 and row[1] == project_name:
                return json.loads(row[2])
    except Exception as e:
        st.error(f"🚨 Cloud Load Error: {e}")
    return None

def delete_project_from_cloud(project_name):
    """Removes a project row from the PROJECTS tab."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        ws = get_or_create_worksheet(doc, PROJECT_SHEET)
        data = ws.get_all_values()
        for i, row in enumerate(data):
            if i > 0 and row[1] == project_name:
                ws.delete_rows(i + 1)
                return True
    except Exception as e:
        st.error(f"🚨 Cloud Delete Error: {e}")
    return False

def save_material_library_to_cloud(df):
    """Overwrites the dedicated MaterialLibrary sheet with current session state."""
    try:
        client = get_gspread_client()
        doc = client.open_by_key(SHEET_ID)
        
        # Explicitly use or create the MaterialLibrary sheet
        ws = get_or_create_worksheet(doc, MATERIAL_SHEET, rows="500", cols="10")
        ws.clear()
        
        # Replace NaN/None with empty strings
        clean_df = df.fillna("")
        
        # Prepare data for update: [header] + [rows]
        data_to_send = [clean_df.columns.values.tolist()] + clean_df.values.tolist()
        ws.update(data_to_send)
        return True
    except Exception as e:
        st.error(f"🚨 Library Sync Error: {e}")
        return False
