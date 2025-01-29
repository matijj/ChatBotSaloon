

from googleapiclient.discovery import build
from google.oauth2 import service_account



import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "keys.json")




# Google Sheets API setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
#SERVICE_ACCOUNT_FILE = "../keys.json"
SAMPLE_SPREADSHEET_ID = "1jw6PUUds9VbdOIyBlNvmehHQFdfNuWteYJBRZwUInQA"

# Initialize Google Sheets API client
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)
sheet = service.spreadsheets()

def read_data(range_name):
    """
    Read data from the specified range in the Google Sheet.
    Args:
        range_name (str): The range to read, e.g., "list!A1:C".
    Returns:
        list: The values from the specified range.
    """
    try:
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=range_name).execute()
        values = result.get("values", [])
        return values
    except Exception as e:
        print(f"Error reading data: {e}")
        return []

def write_data(range_name, values):
    """
    Append data to the specified range in the Google Sheet.
    Args:
        range_name (str): The range to append to, e.g., "list!A1".
        values (list): The data to append, e.g., [["John Doe", "john@example.com", "2025-01-05 14:00:00"]].
    Returns:
        dict: The API response if successful, None otherwise.
    """

    if not values:  # Check for empty or invalid data
        print("No data to write.")
        return None

    try:
        body = {"values": values}
        result = sheet.values().append(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        return result
    except Exception as e:
        print(f"Error writing data: {e}")
        return None




#print(read_data("list!A1:C"))
#
## Test writing
#write_data("list!A1", [["Test Name", "test@example.com", "2025-01-05 14:00:00"]])
#
## Verify the data was written
#print(read_data("list!A1:C"))
