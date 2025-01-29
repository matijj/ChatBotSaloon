"""
calendar_services.py
====================

This module handles Google Calendar integrations and time-slot management for the chatbot application.
It includes functionality to create calendar events, check for free/busy slots, validate date-time inputs,
and convert local times to UTC. These features are essential for managing user appointments and ensuring
availability within the chatbot's scheduling flow.

Key Features:
--------------
1. **Google Calendar Integration**:
   - Event creation with specified details like summary, description, and time.
   - FreeBusy queries to check calendar availability.

2. **Time Management**:
   - Date-time validation and conversion to UTC.
   - Slot-finding logic to suggest alternative times if the requested slot is unavailable.

3. **Dialogflow Context Management**:
   - Functions to update session parameters and prepare Dialogflow contexts for slot-checking and scheduling.

Error Handling:
----------------
Comprehensive error handling is provided to address issues such as:
- Missing or invalid credentials for Google Calendar.
- Invalid or improperly formatted date-time inputs.
- API-related issues during event creation or FreeBusy queries.

Dependencies:
--------------
- `googleapiclient.discovery` for interacting with Google Calendar API.
- `datetime` and `pytz` for time management and conversion.

"""

import os
import logging
import json
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


# Load environment variables
load_dotenv()

CREDENTIALS = os.getenv("CREDENTIALS")
CALENDAR_ID = os.getenv("CALENDAR_ID")

if not CREDENTIALS:
    raise ValueError("CREDENTIALS environment variable is missing.")
if not CALENDAR_ID:
    raise ValueError("CALENDAR_ID environment variable is missing.")

# Parse the credentials JSON
try:
    service_account = json.loads(CREDENTIALS)
except json.JSONDecodeError as e:
    raise ValueError("Failed to parse CREDENTIALS JSON.") from e

# Initialize the Google Calendar client
credentials = Credentials.from_service_account_info(service_account, scopes=["https://www.googleapis.com/auth/calendar"])
calendar = build("calendar", "v3", credentials=credentials)
#


#-------------------------------------------
from datetime import datetime, timedelta
import pytz


#-------------------------------------------------------------------------------------


#------------------------------------------------------------------------------------------------------------


def create_event(summary: str, description: str, start_time: str, time_zone: str = "UTC") -> dict:
    """
    Creates an event in the Google Calendar.

    Parameters:
        - summary (str): Event title.
        - description (str): Event description.
        - start_time (str): Start time in ISO format (e.g., "2025-01-10T10:00:00Z").
        - time_zone (str): Timezone of the event (default: "UTC").

    Returns:
        - dict: The created event details.
    """
    try:
        # Log incoming parameters
        #print(f"[DEBUG] Received parameters: summary={summary}, description={description}, start_time={start_time}, time_zone={time_zone}")

        # Ensure start_time is in UTC
        if 'Z' in start_time or '+' in start_time or '-' in start_time:
            start_datetime_utc = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        else:
            raise ValueError("start_time must include timezone information (e.g., 'Z', '+', or '-')")

        # Calculate event end time (30 minutes duration)
        end_datetime_utc = start_datetime_utc + timedelta(minutes=30)

        # Create the event object
        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_datetime_utc.isoformat(),
                "timeZone":time_zone,
            },
            "end": {
                "dateTime": end_datetime_utc.isoformat(),
                "timeZone": time_zone,
            },
        }

        # Insert the event into the calendar
        event_result = calendar.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        return event_result

    except Exception as e:
        print(f"[ERROR] Error creating event: {e}")
        raise


#------------------------------------------------------------------------------------------------------------------------







#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------

#
def build_slot_check_contexts(session: str, next_context: str, session_parameters: dict, lifespan: int = 1) -> list:
    """
    Builds output contexts for Dialogflow slot-checking and transitions to the next action.

    This function creates a list of context objects required for Dialogflow, including:
    - A specific context indicating the next expected user action (e.g., 'await-slot-confirmation').
    - The session parameters context, which persists session-related data.

    Parameters:
        - session (str): The unique Dialogflow session ID for the current user interaction.
        - next_context (str): The name of the next context to set (e.g., 'await-slot-confirmation').
        - session_parameters (dict): Key-value pairs representing the session data to be retained.
        - lifespan (int): The lifespan (number of interactions) for the contexts. Defaults to 1.

    Returns:
        - list: A list of dictionaries representing Dialogflow output contexts.

    Raises:
        - ValueError: If any of the inputs (session, next_context, or session_parameters) are of incorrect types.
    """

    if not isinstance(session, str):
        raise ValueError("Session must be a string.")
    if not isinstance(next_context, str):
        raise ValueError("Next context must be a string.")
    if not isinstance(session_parameters, dict):
        raise ValueError("Session parameters must be a dictionary.")

    return [
        {
            'name': f'{session}/contexts/{next_context}',
            'lifespanCount': lifespan
        },
        {
            'name': f'{session}/contexts/session-parameters',
            'lifespanCount': lifespan,
            'parameters': session_parameters
        }
    ]



#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------


def get_free_busy(start_time: str, end_time: str, timezone: str) -> list:
    """
    Fetches the busy time slots for a specified time range from Google Calendar.

    This function converts the provided start and end times from the user's local timezone 
    to UTC before querying the Google Calendar FreeBusy API. It retrieves all busy slots 
    within the specified range for the configured calendar.

    Parameters:
        - start_time (str): The start of the time range in ISO format 
          (e.g., "2025-01-16T20:00:00+01:00"). Must include timezone information.
        - end_time (str): The end of the time range in ISO format 
          (e.g., "2025-01-16T20:30:00+01:00"). Must include timezone information.
        - timezone (str): The user's local timezone (e.g., "Europe/Belgrade").

    Returns:
        - list: A list of dictionaries representing busy time slots within the range. 
          Each dictionary contains a "start" and "end" key in ISO format.

    Raises:
        - ValueError: If the `start_time` or `end_time` is not in ISO format or lacks timezone information.
        - Exception: If the Google Calendar API call fails or if another unexpected error occurs.

    Notes:
        - The returned busy slots are in UTC, as required by the Google Calendar FreeBusy API.
        - If an exception occurs, an empty list is returned.
    """


    """
    Fetches the busy slots for a given time range from Google Calendar.
    Converts local times to UTC before querying the API.

    Parameters:
        - start_time (str): Start of the range in ISO format (e.g., "2025-01-16T20:00:00+01:00").
        - end_time (str): End of the range in ISO format (e.g., "2025-01-16T20:30:00+01:00").
        - timezone (str): User's timezone (e.g., "Europe/Belgrade").

    Returns:
        - list: A list of busy slots within the time range.
    """
    try:

        # Convert local times to UTC
        tz = pytz.timezone(timezone)
        start_time_utc = datetime.fromisoformat(start_time).astimezone(pytz.UTC).isoformat()
        end_time_utc = datetime.fromisoformat(end_time).astimezone(pytz.UTC).isoformat()


        # Build the request body for the FreeBusy API
        body = {
            "timeMin": start_time_utc,
            "timeMax": end_time_utc,
            "timeZone": "UTC",  # Google Calendar expects UTC
            "items": [{"id": CALENDAR_ID}],
        }

        # Query the FreeBusy API
        free_busy_response = calendar.freebusy().query(body=body).execute()
        busy_slots = free_busy_response.get("calendars", {}).get(CALENDAR_ID, {}).get("busy", [])
        return busy_slots

    except Exception as e:
        logging.error("[get_free_busy] Unexpected error: %s", e, exc_info=True)
        return []






#-------------------------
#FUNCTION FOR USER PROVIDES DATE TIME AND USER UPDATES DATE TIME


#bez logova
def extract_and_validate_date_time(body: dict, context_name: str, session_parameters: dict) -> tuple[bool, str]:
    """
    Extracts and validates the date-time parameter from the request body.

    Parameters:
        - body (dict): The request body from Dialogflow, containing the user's input and parameters.
        - context_name (str): The name of the context for re-prompting the user if validation fails.
        - session_parameters (dict): The session parameters dictionary where validated values can be stored.

    Returns:
        - tuple: 
            - is_valid (bool): Indicates whether the date-time value is valid.
            - date_time (str): The extracted and validated date-time string, or an empty string if invalid.
    """


    date_time_param = body['queryResult']['parameters'].get('date-time', [])

    if isinstance(date_time_param, list) and len(date_time_param) > 0:
        date_time_value = date_time_param[0].get('date_time', '') if isinstance(date_time_param[0], dict) else date_time_param[0]
    else:
        date_time_value = ''

    if not date_time_value:
        #print("[DEBUG] No date_time_value provided.")
        return False, ''

    return True, date_time_value



#DODAVANJE ZA EUROPIAN STYLE
import re  # For handling normalization









#------------------------------------------------------------------------------------

def convert_to_utc_and_store(date_time: str, session_parameters: dict, timezone: str = "UTC") -> dict:
    """
    Converts the provided date-time to UTC and updates session parameters.

    Parameters:
        - date_time (str): The date-time string to be converted (e.g., "2025-01-10T15:00:00+01:00").
        - session_parameters (dict): A dictionary containing session-specific data. This will be updated with:
            - Original date-time (`date_time`).
            - Converted UTC date-time (`utc_time`).
            - User-specified timezone (`timezone`).
        - timezone (str): The timezone provided by the user (default: "UTC").

    Returns:
        - dict: The updated session_parameters dictionary with the converted UTC time.

    Raises:
        - ValueError: If the date-time format is invalid or conversion fails.

    """


    try:
        # Convert the provided date-time string into a timezone-aware datetime object
        local_time = datetime.fromisoformat(date_time)

        # Convert the local time to UTC
        utc_time = local_time.astimezone(pytz.UTC).isoformat()


        # Update session parameters with original date-time, UTC time, and timezone
        session_parameters['date_time'] = date_time
        session_parameters['utc_time'] = utc_time
        session_parameters['timezone'] = timezone

        return session_parameters
    except Exception as e:
        raise ValueError(f"Invalid date-time format: {e}")


#------------------------------------------------------------------------------------



def find_available_slot(start_time: str, timezone: str, max_attempts: int = 12) -> tuple[bool, dict]:

    """
    Attempts to find an available 30-minute time slot starting from the given start time.

    Parameters:
        - start_time (str): The initial desired start time in ISO format (e.g., "2025-01-10T10:00:00+01:00").
        - timezone (str): The user's timezone (e.g., "Europe/Belgrade").
        - max_attempts (int): The maximum number of 30-minute slots to try (default: 12).

    Returns:
        - tuple:
            - bool: `True` if an available slot is found, `False` otherwise.
            - dict: Details of the available slot if found:
                - "local_time" (datetime): The slot's local start time.
                - "utc_time" (str): The slot's UTC start time in ISO format.
                - "is_original" (bool): `True` if the slot matches the original requested start time, `False` otherwise.

    Notes:
        - Each slot is checked in 30-minute increments starting from the given start time.
        - If no available slot is found within the `max_attempts`, the function returns `False` and an empty dictionary.
    """


    attempts = 0 # Initialize the number of attempts
    while attempts < max_attempts:

        # Calculate the local start time for the current attempt
        start_time_local = datetime.fromisoformat(start_time) + timedelta(minutes=30 * attempts)

        # Convert the local start time to UTC
        start_time_utc = start_time_local.astimezone(pytz.UTC).isoformat()

        # Calculate the UTC end time for the 30-minute slot
        end_time_utc = (start_time_local + timedelta(minutes=30)).astimezone(pytz.UTC).isoformat()


        # Fetch busy slots using the Google Calendar FreeBusy API
        busy_slots = get_free_busy(start_time=start_time_utc, end_time=end_time_utc, timezone=timezone)

        # If no busy slots are found, return the available slot
        if not busy_slots:
            return True, {"local_time": start_time_local, "utc_time": start_time_utc, "is_original": attempts == 0}

        attempts += 1

    return False, {}





