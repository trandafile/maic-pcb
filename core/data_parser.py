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
    """
    Saves or updates a project state in the 'SavedProjects' tab using Service Account.
    """
    try:
        import datetime
        client = gspread.service_account(filename='credenziali-bot.json')
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
        client = gspread.service_account(filename='credenziali-bot.json')
        doc = client.open_by_key(SHEET_ID)
        ws = doc.worksheet("SavedProjects")
        data = ws.get_all_values()
        return [row[1] for i, row in enumerate(data) if i > 0]
    except:
        return []

def load_project_from_cloud(project_name):
    """Loads a specific project by name."""
    try:
        client = gspread.service_account(filename='credenziali-bot.json')
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
        client = gspread.service_account(filename='credenziali-bot.json')
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
        client = gspread.service_account(filename='credenziali-bot.json')
        doc = client.open_by_key(SHEET_ID)
        sheet = doc.sheet1
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"🚨 Library Sync Error: {e}")
        return False
