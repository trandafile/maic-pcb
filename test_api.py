import gspread
from google.oauth2.service_account import Credentials
import traceback

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

try:
    print("Testing auth...")
    creds = Credentials.from_service_account_file('credenziali-bot.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    print("Trying to open 1gX-RaYRxpPgClUkKnBqvoUVKW3cZBaheQpYvh1uFoKA (Material db)")
    doc = client.open_by_key('1gX-RaYRxpPgClUkKnBqvoUVKW3cZBaheQpYvh1uFoKA')
    print("Success! Sheet Title:", doc.title)
except Exception as e:
    print(f"Failed opening material DB: {type(e).__name__} - {e}")

try:
    print("Trying to open 1xzMM4HiKXW6Vp7NAL3feuKjSzb0--YZls2pcHFxVTgI (Mtasks backup)")
    doc2 = client.open_by_key('1xzMM4HiKXW6Vp7NAL3feuKjSzb0--YZls2pcHFxVTgI')
    print("Success! Sheet Title:", doc2.title)
except Exception as e:
    print(f"Failed opening backup DB: {type(e).__name__} - {e}")
