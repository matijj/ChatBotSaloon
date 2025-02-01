"""
action_handlers.py

This module defines the action handlers for processing Dialogflow intents.

Each handler function corresponds to a specific action defined in Dialogflow
and provides the appropriate response, such as rich content messages,
user prompts, or Google Calendar integrations.

Purpose:
---------
- To manage conversational flows initiated by Dialogflow intents.
- To handle user inputs, validate data, and produce relevant responses.
- To integrate with external systems like Google Calendar for scheduling.

Structure:
-----------
1. **General Intent Handlers**:
    - Handles welcome messages and fallback scenarios.

2. **Scheduling Handlers**:
    - Manages the flow for booking appointments, including capturing user
      details (name, email, date, time, and notes).

3. **Update Handlers**:
    - Allows users to update specific fields (name, email, date-time, note)
      for an existing appointment.

4. **Note Handlers**:
    - Handles interactions related to adding or skipping notes.

5. **Product Handlers**:
    - Provides information about specific products using rich content responses.

6. **Slot Update Handlers**:
    - Manages updates to time slots, ensuring availability and user confirmation.

Error Handling:
----------------
- Includes error handling for invalid inputs, missing parameters, or
  unexpected errors during execution.
- Returns user-friendly error messages where applicable.

Dependencies:
--------------
- `calendar_services`: For Google Calendar integration (e.g., event creation).
- `helper_functions`: For common utilities like session extraction or validation.

"""



from utils.helper_functions import format_dialogflow_response, format_rich_response_with_chips, format_dialogflow_response_with_image_and_chips, is_valid_email, extract_session_parameters, validate_name, build_contexts, extract_session, extract_output_contexts, is_within_working_hours


from utils.config import WORKING_HOURS

import re
from utils.calendar_services import extract_and_validate_date_time,convert_to_utc_and_store,find_available_slot
import logging




def default_welcome_intent(body: dict) -> dict:
    """
    Handles the default welcome intent from Dialogflow.

    Purpose:
    ---------
    This function responds to the user's initial interaction, introducing the bot's capabilities and
    providing options for next steps using rich content with chips.

    Parameters:
    ------------
    - body (dict): The request body from Dialogflow containing session information and user inputs.

    Returns:
    ---------
    - dict: A rich response formatted for Dialogflow, including a welcome message and action chips.

    Error Handling:
    ----------------
    - Captures and logs unexpected errors.
    - Returns user-friendly error messages in case of failures.
    """

    try:
        # Step 1: Extract the Dialogflow session ID from the request body
        session = extract_session(body)

        # Step 2: Build the response using a rich content formatter
        response_data = format_rich_response_with_chips(
            [
                "Hi there! I’m here to assist you. Here’s what I can do for you:",
                "- Provide our business hours and location.",
                "- Tell you about our services.",
                "- Help you schedule an appointment!",
                "- Type Products if you want product info.",
                "What would you like to do?"
            ],
            chips=["Schedule Appointment", "Services", "Products"]
        )

        return response_data



    except ValueError as e:
        # Handle specific errors (e.g., issues with the session extraction)
        return {"error": str(e)}


    except Exception as e:
        logging.error("[default_welcome_intent] Unexpected error:", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }






def handle_user_wants_to_schedule_appointment(body: dict) -> dict:
    """
    Handles the "user wants to schedule an appointment" intent in Dialogflow.

    Purpose:
    --------
    This function initializes session parameters for scheduling an appointment and 
    sets up the appropriate contexts to guide the user through the scheduling process. 
    The first step is to ask for the user's name.

    Parameters:
    ------------
    - body (dict): The request body from Dialogflow, containing session information and user input.

    Returns:
    ---------
    - dict: A response formatted for Dialogflow, including a prompt for the user's name 
      and initialized session parameters.

    Steps:
    ------
    1. Extract the session ID from the Dialogflow request.
    2. Initialize session parameters, including placeholders for name, email, date-time, note, UTC time, and timezone.
    3. Set up the required output contexts:
       - `await-name`: To prompt the user for their name.
       - `session-parameters`: To store session data persistently.
    4. Build a response asking the user for their name.

    Error Handling:
    ---------------
    - Returns a user-friendly message for invalid sessions (e.g., missing or malformed session data).
    - Logs unexpected errors and returns a generic error message to Dialogflow.

    Dependencies:
    --------------
    - Utilizes `extract_session` for extracting the session ID.
    - Uses `format_dialogflow_response` for constructing the response for Dialogflow.
    """

    try:
        # Step 1: Extract session from the request body
        session = extract_session(body)

        # Step 2: Initialize session parameters
        session_parameters = {
            "person": "",
            "email": "",
            "date_time": "",  # Placeholder for date and time
            "note": "No note",  # Default value for note
            "utc_time": "",  # New placeholder for UTC time
            "timezone": ""   # New placeholder for user timezone
        }

        # Step 3: Set up output contexts for Dialogflow
        output_contexts = [
            {
                'name': f'{session}/contexts/await-name',
                'lifespanCount': 1  # Set next expected step
            },
            {
                'name': f'{session}/contexts/session-parameters',
                'lifespanCount': 99,  # Preserve session data
                'parameters': session_parameters
            }
        ]

        # Step 4: Build the Dialogflow response
        response_data = format_rich_response_with_chips(
            [
                "Great! To schedule, let’s start with your name. What’s your name?"
            ],
            chips=["Restart Chat"],
            output_contexts=output_contexts
        )






        # Step 5: Return the constructed response
        return response_data

    except ValueError:
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Invalid session."]}}
            ]
        }
    except Exception as e:
        logging.error("[handle_user_wants_to_schedule_appointment] Unexpected error:", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }



#------------------------------------------------------------------------------------------------

#RADI  

def handle_user_provides_name(body: dict) -> dict:
    """
    Handles the "user provides name" intent in Dialogflow.

    Purpose:
    --------
    This function processes the user's provided name, validates it, updates the session parameters,
    and transitions to the next step of the flow (collecting the email).

    Parameters:
    ------------
    - body (dict): The request body from Dialogflow, containing session information, contexts, and user input.

    Returns:
    ---------
    - dict: A response formatted for Dialogflow, either:
        - Prompting for the next input (email) if the name is valid.
        - Re-asking for a valid name if the input fails validation.

    Steps:
    ------
    1. Extract session and output contexts from the Dialogflow request body.
    2. Retrieve existing session parameters from the output contexts.
    3. Extract and validate the user-provided name:
       - If invalid, prompt the user to provide a valid name again.
       - If valid, update the session parameters with the user's name.
    4. Transition to the next step by setting the context to `await-email`.
    5. Construct and return the Dialogflow response.

    Error Handling:
    ---------------
    - Handles missing or invalid session/context data gracefully by returning a fallback response.
    - Logs unexpected errors and provides a generic error message to Dialogflow.

    Dependencies:
    --------------
    - Utilizes utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `validate_name`
        - `build_contexts`
        - `format_dialogflow_response`
    """
    try:
        # Step 1: Extract session and output contexts from the request body
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)

        # Step 2: Extract session parameters from the output contexts
        session_parameters = extract_session_parameters(output_contexts)

        # Step 3: Extract user-provided name from the request
        parameters = body['queryResult'].get('parameters', {})
        user_name = parameters.get('person.original', '') or session_parameters.get('person.original', '')
        user_name = user_name.strip()  # Remove leading/trailing spaces

        logging.info(f"[handle_user_provides_name] Extracted user name: '{user_name}'")

        # Step 4: Validate the name
        if not validate_name(user_name):
            logging.warning("[handle_user_provides_name] Invalid name detected.")
            response_data = format_dialogflow_response(
                ["Hmm, that doesn’t look like a valid name. Please avoid special characters or numbers."],
                [
                    {
                        'name': f'{session}/contexts/await-name',
                        'lifespanCount': 1  # Keep asking for a valid name
                    },
                    {
                        'name': f'{session}/contexts/session-parameters',
                        'lifespanCount': 99 # Retain the session parameters context
                    }
                ]
            )
            return response_data

        # Step 5: Update session-parameters with the validated name
        session_parameters['person'] = user_name
        logging.info(f"[handle_user_provides_name] Updated session parameters: {session_parameters}")

        # Step 6: Build updated contexts to transition to the next step (email collection)
        output_contexts = build_contexts(session, 'await-email', session_parameters)

        # Step 7: Build and return the response for Dialogflow
        response_data = format_dialogflow_response(
            [
                f"Thanks for your name, {user_name}! What’s your email?"
            ],
            output_contexts
        )
        return response_data

    except ValueError as ve:
        # Handle cases where session extraction or parameters are invalid
        logging.warning(f"[handle_user_provides_name] ValueError: {ve}")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }

    except Exception as e:
        # Log unexpected errors and return a generic fallback response
        logging.error("[handle_user_provides_name] Unexpected error:", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }




#------------------------------------------------------------------------
#USER PROVIDES EMAIL 
#---------------------------------------------------------------------------

def handle_user_provides_email(body: dict) -> dict:
    """
    Handles the "user provides email" intent in Dialogflow.

    Purpose:
    --------
    This function processes the user's provided email address, validates it,
    updates the session parameters, and transitions to the next step of the flow (collecting date and time).

    Parameters:
    ------------
    - body (dict): The request body from Dialogflow, containing session information, contexts, and user input.

    Returns:
    ---------
    - dict: A response formatted for Dialogflow, either:
        - Prompting for the next input (date and time) if the email is valid.
        - Re-asking for a valid email if the input fails validation.

    Steps:
    ------
    1. Extract session, output contexts, and session parameters from the Dialogflow request body.
    2. Retrieve and validate the user-provided email address:
       - If invalid, prompt the user to provide a valid email.
       - If valid, update the session parameters with the email.
    3. Transition to the next step by setting the context to `await-date-time`.
    4. Construct and return the Dialogflow response.

    Error Handling:
    ---------------
    - Handles missing or invalid session/context data gracefully by returning a fallback response.
    - Logs unexpected errors and provides a generic error message to Dialogflow.

    Dependencies:
    --------------
    - Utilizes utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `is_valid_email`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        # Step 1: Extract session, output contexts, and session parameters
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)

        # Step 2: Extract and validate email
        user_email = body['queryResult']['parameters'].get('email.original', '') or session_parameters.get('email.original', '')
        if not is_valid_email(user_email):
            # If email is invalid, prompt the user to try again
            return format_dialogflow_response(
                ["Hmm, that doesn’t look like a valid email address. Could you try again?"],
                [
                    {'name': f'{session}/contexts/await-email-update', 'lifespanCount': 1},
                    {'name': f'{session}/contexts/session-parameters', 'lifespanCount': 99, 'parameters': session_parameters}
                ]
            )

        # Step 3: Update session parameters with valid email
        session_parameters['email'] = user_email


        # Step 4: Build updated contexts to transition to the next step (date and time collection)
        output_contexts = build_contexts(session, 'await-date-time', session_parameters)


        # Step 5: Construct and return the Dialogflow response
        response_data = format_dialogflow_response(
            ["Thanks! What date and time works for you? Example: Tomorrow at 1 pm or January 10th at 22h."],
            output_contexts
        )
        return response_data

    except ValueError as ve:
        logging.warning(f"[handle_user_provides_email] Validation error: {ve}")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }

    except Exception as e:
        logging.error("[handle_user_provides_email] Unexpected error:", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }




#---------------------------------------------------------------------------

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------



#USER PROVIDES TIME
from utils.calendar_services import get_free_busy,build_slot_check_contexts

from datetime import datetime, timedelta


import pytz


#-------------------------------------------------


def handle_user_provides_date_time(body: dict) -> dict:
    try:
        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)

        # Step 2: Validate and extract date-time input
        is_valid, date_time_value = extract_and_validate_date_time(body, 'await-date-time', session_parameters)
        if not is_valid:
            # If validation fails, re-prompt the user for a valid date and time
            logging.warning("[handle_user_provides_date_time] Invalid date-time input.")
            return format_dialogflow_response(
                ["I didn’t catch that. Can you provide a date and time like 'Tomorrow at 1 pm'?"],
                build_contexts(session, 'await-date-time', session_parameters)
            )


            #NEWWWWWWWWWWWWWW


		# Parse the provided date-time value into a datetime object
        parsed_date_time = datetime.fromisoformat(date_time_value)

		# Validate and normalize the timezone
        user_timezone = session_parameters.get("timezone", "UTC")  # Default to UTC if missing
        if not user_timezone or user_timezone not in pytz.all_timezones:
            logging.warning(f"[handle_user_provides_date_time] Invalid or missing timezone '{user_timezone}'. Falling back to UTC.")
            user_timezone = "UTC"

		# Ensure both times are timezone-aware
        current_time = datetime.now(pytz.timezone(user_timezone))  # Current time in user's timezone
        parsed_date_time = parsed_date_time.astimezone(pytz.timezone(user_timezone))  # Adjust parsed date-time to user's timezone

		# Compare the parsed date-time with the current time
        if parsed_date_time < current_time:
            logging.warning(f"[handle_user_provides_date_time] The requested date-time {parsed_date_time} is in the past.")
            return format_dialogflow_response(
				["You can’t schedule for a past date or time. Please choose a future date and time."],
                build_contexts(session, 'await-date-time', session_parameters)
                )


   

   #----------------

        # NEW: Step 3 - Validate working hours
        user_timezone = session_parameters.get("timezone", "Europe/Belgrade")

        if not user_timezone:  # If timezone is empty, fallback to the default
            logging.warning("[handle_user_provides_date_time] Timezone is empty. Defaulting to Europe/Belgrade.")
            user_timezone = "Europe/Belgrade"



		# Use the date_time_value with working hours validation
        if not is_within_working_hours(date_time_value, timezone=user_timezone):
            logging.warning(f"[handle_user_provides_date_time] Time {date_time_value} is outside working hours.")
            return format_dialogflow_response(
                    [f"Sorry, that time is outside our working hours ({WORKING_HOURS['start']}:00 to {WORKING_HOURS['end']}:00). Please provide another time."],
                    build_contexts(session, 'await-date-time', session_parameters)
                    )


        # Step 4: Convert the valid date-time to UTC and update session parameters
        try:
            session_parameters = convert_to_utc_and_store(
                date_time_value, session_parameters, timezone="Europe/Belgrade"
            )
        except ValueError as e:
            logging.error("[handle_user_provides_date_time] Invalid date-time format.", exc_info=True)
            return format_dialogflow_response(
                ["The date-time format is invalid. Please provide it in a valid format like 'Tomorrow at 1 pm'."],
                build_contexts(session, 'await-date-time', session_parameters)
            )
        except Exception as e:
            logging.error("[handle_user_provides_date_time] Unexpected error during UTC conversion.", exc_info=True)
            return format_dialogflow_response(
                ["An error occurred while processing your date and time. Please try again."],
                build_contexts(session, 'await-date-time', session_parameters)
            )

        # Step 5: Check slot availability
        try:
            is_slot_found, slot_details = find_available_slot(
                session_parameters['date_time'], session_parameters['timezone'], max_attempts=12
            )
        except Exception as e:
            logging.error("[handle_user_provides_date_time] Error checking slot availability.", exc_info=True)
            return format_dialogflow_response(
                ["An error occurred while checking availability. Please try again later."],
                build_contexts(session, 'await-date-time', session_parameters)
            )

        # Step 6: Handle slot availability
        if is_slot_found:
            # Update session parameters with the confirmed or suggested slot
            session_parameters['date_time'] = slot_details['local_time'].isoformat()
            session_parameters['utc_time'] = slot_details['utc_time']

            if slot_details['is_original']:
                # Original slot is available
                output_contexts = build_contexts(session, 'await-note-action', session_parameters)
                return format_rich_response_with_chips(
                    ["Great! The time you selected is available. Do you want to add a note?"],
                    chips=["Yes", "No"],
                    output_contexts=output_contexts
                )
            else:
                # Suggest an alternative slot if the original is unavailable
                suggested_local_time = slot_details['local_time'].strftime('%Y-%m-%d at %I:%M %p')  # Example: 2025-01-29 at 11:00 AM


                requested_time = datetime.fromisoformat(date_time_value).strftime('%Y-%m-%d at %I:%M %p')  # Example: 2025-01-29 at 10:00 AM


                output_contexts = build_contexts(session, 'await-slot-confirmation', session_parameters)
                return format_rich_response_with_chips(
                    [
						f"The time you requested ({requested_time}) is unavailable.",
						f"However, the following slot is available:",
						f"Date/Time: {suggested_local_time}",
						"Would you like to book this slot instead?"

                    ],
                    chips=["Yes", "No"],
                    output_contexts=output_contexts
                )

        # Step 7: Handle no slots available
        logging.warning("[handle_user_provides_date_time] No slots available.")
        return format_dialogflow_response(
            ["I'm sorry, no slots are available within the next 6 hours. Please provide another time."],
            build_contexts(session, 'await-date-time', session_parameters)
        )

    except ValueError:
        # Handle invalid session or output contexts
        logging.warning("[handle_user_provides_date_time] Invalid session or output contexts.")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }
    except Exception as e:
        # Handle unexpected runtime errors
        logging.error("[handle_user_provides_date_time] Unexpected error occurred.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }



#----------------------------------------------------------------------------------------


#SA ERORR HANDLINGOM
def handle_user_confirms_slot(body: dict) -> dict:
    """
    Handles the "user confirms slot" intent in Dialogflow.

    Purpose:
    --------
    This function processes the user's confirmation of a suggested date and time slot.
    It validates the session parameters to ensure the slot details are present and then
    updates the session to proceed with the next step in the flow (e.g., adding a note).

    Parameters:
    ------------
    - body (dict): The request body from Dialogflow, containing session information, contexts, and user input.

    Returns:
    ---------
    - dict: A response formatted for Dialogflow:
        - Confirms the slot and prompts the user to add a note with Yes/No options.
        - Requests the user to re-enter date and time if session parameters are incomplete.
        - Returns error messages for validation failures or unexpected runtime errors.

    Steps:
    ------
    1. Extract session ID, active contexts, and session parameters from the Dialogflow request body.
    2. Validate the session parameters to ensure a valid `date_time` is available.
    3. Update session parameters with the confirmed date and time.
    4. Build updated contexts to guide the user to the next step in the conversation.
    5. Construct a rich response with chips for user options (Yes/No).

    Error Handling:
    ---------------
    - Returns user-friendly messages for missing or invalid `date_time`.
    - Handles unexpected errors with generic fallback responses.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_rich_response_with_chips`
        - `format_dialogflow_response`
    """

    try:
        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)

        # Step 2: Validate that the 'date_time' exists in session parameters
        confirmed_date_time = session_parameters.get('date_time')
        if not confirmed_date_time:
            # If 'date_time' is missing, re-prompt the user for input
            logging.warning("[handle_user_confirms_slot] Missing 'date_time' in session parameters.")
            return format_dialogflow_response(
                ["It seems the date and time are missing. Please provide the details again."],
                build_contexts(session, 'await-date-time', session_parameters)
            )

        # Step 3: Update session parameters with the confirmed date and time
        session_parameters['confirmed_date_time'] = confirmed_date_time

        # Step 4: Prepare updated contexts for guiding the user to the next step
        output_contexts = build_contexts(session, 'await-note-action', session_parameters)

        # Step 5: Build response with Yes/No chips
        response_data = format_rich_response_with_chips(
            ["Great. Do you want to add a note?"],
            chips=["Yes", "No"],
            output_contexts=output_contexts
        )

        return response_data

    except ValueError as e:
        logging.warning("[handle_user_confirms_slot] Validation error.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }
    except Exception as e:
        logging.error("[handle_user_confirms_slot] Unexpected error occurred.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }





#|----------------------------------------------------------------------------------------------------

#HANDLE_USER_DENIES_SLOT

def handle_user_denies_slot(body: dict) -> dict:
    """
    Handles the scenario where the user denies the suggested date and time slot.

    Purpose:
    --------
    When a user denies the suggested time slot, this function guides them back
    to providing a new date and time that works better for their schedule.

    Parameters:
    ------------
    - body (dict): The Dialogflow webhook request payload containing user input,
      session details, and output contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user
      to provide a new date and time for scheduling.

    Steps:
    ------
    1. Extract session, contexts, and parameters from the Dialogflow request payload.
    2. Inform the user that their slot was denied and prompt them for a new date and time.
    3. Transition back to the `await-date-time` context.
    4. Construct and return the response with the updated context.

    Error Handling:
    ---------------
    - Handles missing or invalid session/contexts with user-friendly error messages.
    - Logs unexpected runtime errors and provides a fallback response.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)

        # Step 2: Prepare the response message for the user
        message = (
            "Okay, no problem! What date and time works best for you? "
            "You can say something like 'Tomorrow at 2 pm' or 'January 20th at 10h'."
        )

        # Step 3: Transition back to 'await-date-time' context
        output_contexts = build_contexts(session, 'await-date-time', session_parameters)

        # Step 4: Construct the response to prompt for a new date and time
        response_data = format_dialogflow_response(
            [message],
            output_contexts
        )

        return response_data

    except ValueError:
        logging.warning("[handle_user_denies_slot] Invalid session or output contexts.")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }
    except Exception as e:
        logging.error("[handle_user_denies_slot] Unexpected error occurred.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }




#---------------------------------------------------------------------------

def handle_user_denies_note(body: dict) -> dict:
    """
    Handles the scenario where the user denies adding a note.

    Purpose:
    --------
    When the user indicates that they do not want to add a note,
    this function updates the session parameters accordingly and
    prompts the user to confirm the information collected so far.

    Parameters:
    ------------
    - body (dict): The Dialogflow webhook request payload containing user input,
      session details, and output contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, displaying the
      collected information and asking if the user wants to update anything.

    Steps:
    ------
    1. Extract session, contexts, and session parameters from the Dialogflow request payload.
    2. Update the session parameters to indicate "No note."
    3. Display a confirmation message summarizing the collected information.
    4. Provide the user with options (Yes/No) to confirm or update the information.

    Error Handling:
    ---------------
    - Handles missing session parameters with user-friendly error messages.
    - Logs unexpected runtime errors and provides a fallback response.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_rich_response_with_chips`
    """

    try:
        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)

        # Step 2: Ensure session parameters exist
        session_parameters = extract_session_parameters(output_contexts)
        if not session_parameters:
            logging.warning("[handle_user_denies_note] Missing session parameters.")
            return {
                "fulfillmentMessages": [
                    {"text": {"text": ["Session parameters are missing. Please try again."]}}
                ]
            }

        # Step 3: Update session parameters with "No note"
        session_parameters['note'] = "No note"

        # Step 4: Safely extract parameters for the confirmation message
        name = session_parameters.get("person", "unknown")
        email = session_parameters.get("email", "unknown")
        date_time = session_parameters.get("date_time", "unknown")
        if isinstance(date_time, dict):  # Handle if date_time is a dictionary
            date_time = date_time.get("date_time", "unknown")
        note = session_parameters.get("note", "No note")

        # Step 5: Prepare confirmation message
        confirmation_message = (
            f"Great! Here’s the information I have:\n"
            f"- Name: {name}\n"
            f"- Email: {email}\n"
            f"Date/Time: {datetime.fromisoformat(date_time).strftime('%Y-%m-%d at %I:%M %p') if date_time != 'unknown' else 'unknown'}\n"

            f"- Note: {note}\n"
            "Do you want to update anything?"
        )

        # Step 6: Update contexts for the next step (awaiting confirmation)
        output_contexts = build_contexts(session, 'await-confirmation', session_parameters)

        # Step 7: Build response with Yes/No chips
        response_data = format_rich_response_with_chips(
            [confirmation_message],
            chips=["Yes", "No"],
            output_contexts=output_contexts
        )

        return response_data

    except ValueError:
        logging.warning("[handle_user_denies_note] Invalid session or output contexts.")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }
    except Exception as e:
        logging.error("[handle_user_denies_note] Unexpected error occurred.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }





#------------------------------------------------------------------------------------------
def handle_user_confirms_note(body: dict) -> dict:
    """
    Handles the scenario where the user confirms they want to add a note.

    Purpose:
    --------
    When the user confirms their intent to add a note, this function:
    - Extracts and validates the session parameters.
    - Prepares updated contexts for Dialogflow to indicate the next step (awaiting note input).
    - Builds a response prompting the user to provide the note.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user input, session details, 
      and output contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user to provide a note.

    Steps:
    ------
    1. Extract session ID and output contexts from the Dialogflow payload.
    2. Validate the presence of session parameters.
    3. Update the output contexts for the next step (await-note).
    4. Build and return a response prompting the user to provide the note.

    Error Handling:
    ---------------
    - Handles missing or invalid session parameters with user-friendly error messages.
    - Logs unexpected runtime errors and provides a fallback response.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)

        # Step 2: Extract session parameters (ensure they're valid)
        session_parameters = extract_session_parameters(output_contexts)
        if not session_parameters:
            logging.warning("[handle_user_confirms_note] Session parameters are missing or invalid.")
            return {
                "fulfillmentMessages": [
                    {"text": {"text": ["Something went wrong. Please try again later."]}}
                ]
            }

        # Step 3: Build updated contexts for the next step (awaiting note input)
        output_contexts = build_contexts(session, 'await-note', session_parameters)

        # Step 4: Build response to ask for the note
        response_data = format_dialogflow_response(
            ["Please provide the note."],
            output_contexts
        )
        return response_data

    except ValueError:
        logging.warning("[handle_user_confirms_note] Invalid session or output contexts.")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }
    except Exception as e:
        logging.error("[handle_user_confirms_note] Unexpected error occurred.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }


 


#----------------------------------------------------------------------

def handle_user_provides_note(body: dict) -> dict:
    """
    Handles the scenario where the user provides a note during a Dialogflow interaction.

    Purpose:
    --------
    This function:
    - Extracts and validates the user-provided note.
    - Updates session parameters with the note.
    - Prepares a summary of all collected information (name, email, date/time, and note).
    - Prompts the user to confirm or update their information.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user input, session details, 
      and output contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, providing a confirmation message 
      and Yes/No options for further updates.

    Steps:
    ------
    1. Extract session ID and output contexts from the Dialogflow payload.
    2. Retrieve session parameters and validate them.
    3. Extract the note provided by the user (or assign a default if missing).
    4. Store the note in session parameters and prepare a summary of all information collected.
    5. Build updated contexts for the next step (awaiting confirmation).
    6. Return a response with a confirmation message and Yes/No chips.

    Error Handling:
    ---------------
    - Handles missing or invalid session parameters with user-friendly error messages.
    - Logs unexpected runtime errors and provides a fallback response.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_rich_response_with_chips`
    """

    try:
        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)

        # Step 2: Extract and validate the user-provided note
        user_note = body['queryResult']['parameters'].get('any', '').strip()
        if not user_note:
            user_note = "No note provided"

        # Step 3: Store the note in session parameters
        session_parameters['note'] = user_note

        # Step 4: Extract other session parameters for summary
        name = session_parameters.get("person", "unknown")
        email = session_parameters.get("email", "unknown")
        #date_time_data = session_parameters.get("date_time", "unknown")
        #date_time = date_time_data.get("date_time", "unknown") if isinstance(date_time_data, dict) else date_time_data

        date_time = session_parameters.get("date_time", "unknown")


        if date_time != "unknown":
            try:
                # Format date-time into a readable format (e.g., "2025-01-29 10:00 h")
                date_time = datetime.fromisoformat(date_time).strftime("%Y-%m-%d %H:%M h")
            except ValueError:
                logging.warning("[handle_user_provides_note] Invalid date_time format, using raw value.")





        note = session_parameters['note']

        # Step 5: Prepare the confirmation message with the collected information
        confirmation_message = (
            f"Great! Here’s the information I have:\n"
            f"- Name: {name}\n"
            f"- Email: {email}\n"
            f"- Date and Time: {datetime.fromisoformat(date_time).strftime('%Y-%m-%d at %I:%M %p') if date_time != 'unknown' else 'unknown'}\n"
            f"- Note: {note}\n"
            "Do you want to update anything?"

        )



        # Step 6: Build updated contexts for the next step
        output_contexts = build_contexts(session, 'await-confirmation', session_parameters)

        # Step 7: Build response with confirmation message and Yes/No chips
        response_data = format_rich_response_with_chips(
            [confirmation_message],
            chips=["Yes", "No"],
            output_contexts=output_contexts
        )
        return response_data

    except ValueError:
        logging.warning("[handle_user_provides_note] Invalid session or output contexts.")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong. Please try again later."]}}
            ]
        }
    except Exception as e:
        logging.error("[handle_user_provides_note] Unexpected error occurred.", exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }

#------------------------------------------------------------------------------------------

#------------------------------------------------
#NOVI USER NO CHANGE SA CALENDAROM UMESTO SHEETOM

from datetime import datetime
from utils.calendar_services import create_event
from utils.helper_functions import extract_session_parameters


#ZBOG INSOMNIE NE VALJA DODAO SI OVAJ DOLE ZBOG TOGa
def handle_user_confirms_no_changes(body: dict) -> dict:
    """
    Handles the scenario where the user confirms that no changes are needed.
    This function validates the provided details, creates a calendar event,
    and sends a confirmation response.

    Purpose:
    --------
    - Extract and validate session details.
    - Convert local time to UTC if needed.
    - Create a Google Calendar event for the appointment.
    - Return a confirmation message with the appointment details and calendar link.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing session data,
      user inputs, and output contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, including the
      appointment confirmation details.

    Steps:
    ------
    1. Extract session and output contexts from the payload.
    2. Validate and retrieve key session parameters (name, email, date/time, etc.).
    3. Handle missing or invalid UTC time by converting from local time.
    4. Create an event in Google Calendar using the validated data.
    5. Return a confirmation response with the event details.

    Error Handling:
    ---------------
    - Handles missing or invalid date/time inputs gracefully.
    - Logs errors during calendar event creation and provides fallback responses.
    - Handles unexpected runtime errors with a user-friendly error message.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `create_event`
        - `format_dialogflow_response`
    - External libraries:
        - `pytz` for timezone conversion.
        - `datetime` for date/time manipulation.
    """

    try:
        logging.info("[handle_user_confirms_no_changes] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)

        # Step 2: Extract necessary fields with defaults
        name = session_parameters.get("person", "unknown")
        email = session_parameters.get("email", "unknown")
        note = session_parameters.get("note", "No note provided")
        date_time = session_parameters.get("date_time", "unknown")  # User's local time
        timezone = session_parameters.get("timezone", "UTC")
        utc_time = session_parameters.get("utc_time", "")

        logging.info(
            "[handle_user_confirms_no_changes] Extracted fields: name=%s, email=%s, note=%s, date_time=%s, timezone=%s, utc_time=%s",
            name, email, note, date_time, timezone, utc_time
        )

        # Step 3: Validate utc_time or convert from local time if missing
        if not utc_time:
            if date_time == "unknown":
                raise ValueError("Missing date_time and utc_time in session parameters.")

            logging.warning("[handle_user_confirms_no_changes] utc_time missing. Attempting conversion from date_time: %s", date_time)
            try:
                local_time = datetime.fromisoformat(date_time)
                utc_time = local_time.astimezone(pytz.UTC).isoformat()
                session_parameters['utc_time'] = utc_time
                logging.info("[handle_user_confirms_no_changes] Converted local time to utc_time: %s", utc_time)
            except Exception as e:
                # Handle errors during date-time conversion
                logging.error("[handle_user_confirms_no_changes] Error converting date_time to UTC: %s", e, exc_info=True)
                return format_dialogflow_response(
                    ["There was an issue processing the date and time. Please try again."],
                    []
                )

        # Step 4: Create the calendar event
        try:
            event_details = {
                "summary": f"New appointment for {name}",
                "description": f"{email}, {note}",
                "start_time": utc_time,  # Use UTC for Google Calendar API
            }
            logging.info("[handle_user_confirms_no_changes] Creating calendar event with details: %s", event_details)

            event_data = create_event(
                summary=event_details["summary"],
                description=event_details["description"],
                start_time=event_details["start_time"]
            )
            logging.info("[handle_user_confirms_no_changes] Event created successfully: %s", event_data)
        except Exception as e:
            logging.error("[handle_user_confirms_no_changes] Error creating calendar event: %s", e, exc_info=True)
            return format_dialogflow_response(
                [
                    "Your details were confirmed but the appointment could not be added to the calendar. "
                    "Please try again later."
                ],
                []
            )

        # Step 5: Build confirmation message with appointment details
        confirmation_message = (
            f"Awesome! Your appointment is all set:\n"
            f"- Name: {name}\n"
            f"- Email: {email}\n"

            f"Date/Time: {datetime.fromisoformat(date_time).strftime('%Y-%m-%d at %I:%M %p')}\n"

            f"- Note: {note}\n"
            #f"Calendar link: {event_data.get('htmlLink', 'N/A')}\n"
            "Feel free to reach out if you need anything else. Goodbye for now!"
        )
        logging.info("[handle_user_confirms_no_changes] Confirmation message prepared: %s", confirmation_message)

        # Step 6: Build response to send back to Dialogflow
        response_data = format_dialogflow_response([confirmation_message], [])
        logging.info("[handle_user_confirms_no_changes] Response data: %s", response_data)

        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_confirms_no_changes] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong. Please try again later."],
            []
        )
    except Exception as e:
        logging.error("[handle_user_confirms_no_changes] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )


#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------





def handle_user_wants_to_update(body: dict) -> dict:
    """
    Handles the scenario where the user indicates they want to update an existing appointment detail.

    Purpose:
    --------
    - Extract and validate session details from the incoming Dialogflow webhook payload.
    - Prompt the user with options to update specific fields (e.g., name, email, date-time, or note).
    - Set up the appropriate contexts for Dialogflow to continue the conversation.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing session data, user inputs, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, including update prompts and options.

    Steps:
    ------
    1. Extract session and validate output contexts.
    2. Retrieve session parameters for the current appointment.
    3. Build updated contexts for the next step (await-field).
    4. Prompt the user with options to update specific fields using chips.

    Error Handling:
    ---------------
    - Handles missing or invalid session details gracefully.
    - Logs and responds to unexpected runtime errors with a user-friendly error message.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_rich_response_with_chips`
    """

    try:
        logging.info("[handle_user_wants_to_update] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)

        # Validate that outputContexts exists and is not empty
        if not output_contexts:
            logging.warning("[handle_user_wants_to_update] Missing or empty outputContexts in request.")
            return format_dialogflow_response(
                ["I couldn't find enough information to proceed. Can you try again?"],
                []
            )

        # Step 2: Extract session parameters from the output contexts
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_wants_to_update] Retrieved session parameters: %s", session_parameters)

        # Extract relevant fields from session parameters
        name = session_parameters.get("person", "unknown")
        email = session_parameters.get("email", "unknown")
        note = session_parameters.get("note", "No note provided")
        date_time = session_parameters.get("date_time", "unknown")



        # Step 3: Format the date_time field into a readable format
        if date_time != "unknown":
            try:
                # Convert ISO format to readable format (e.g., "2025-01-29 10:00")
                date_time = datetime.fromisoformat(date_time).strftime("%Y-%m-%d %H:%M") + " h"
                
            except ValueError:
                logging.warning("[handle_user_wants_to_update] Invalid date_time format, using raw value.")
                # Keep the raw value if formatting fails



        prompt = (
            "Here’s the information I have so far:\n\n"
            f"📋 Name: {name}\n"
            f"📧 Email: {email}\n"
            f"📅 Date/Time: {date_time}\n"
            f"📝 Note: {note}\n\n"
            "What would you like to update? You can choose from the following options:"
        )



        # Step 4: Build updated contexts for the next step
        output_contexts = build_contexts(session, 'await-field', session_parameters)

        # Step 5: Build response with chips for updating fields
        response_data = format_rich_response_with_chips(
            [prompt],
            chips=["Name", "Email", "Date-Time", "Note"],
            output_contexts=output_contexts
        )
        logging.info("[handle_user_wants_to_update] Response data prepared.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_wants_to_update] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_wants_to_update] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )






#------------------------------------------------------------------------------------------
#RESPONSE FOR USER CHOOSES NAME FOR UPGRADE


def handle_user_chooses_name(body: dict) -> dict:
    """
    Handles the scenario where the user chooses to update their name.

    Purpose:
    --------
    - Extracts the session details and current name from the Dialogflow webhook payload.
    - Prompts the user to confirm or provide the updated name.
    - Prepares the response and updated contexts for Dialogflow to handle the next step.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing session data, user inputs, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user to update their name.

    Steps:
    ------
    1. Extract the session and validate output contexts.
    2. Retrieve the current name from session parameters.
    3. Prompt the user to provide a new name if the current name is missing or unknown.
    4. Update the contexts to guide Dialogflow to the next step (await-name-update).

    Error Handling:
    ---------------
    - Handles missing or invalid session details gracefully.
    - Logs and responds to unexpected runtime errors with a user-friendly error message.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        logging.info("[handle_user_chooses_name] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)

        # Validate outputContexts
        output_contexts = extract_output_contexts(body)
        if not output_contexts:
            logging.warning("[handle_user_chooses_name] Missing or empty outputContexts in request.")
            return format_dialogflow_response(
                ["I couldn't retrieve the current information. Please try again."],
                []
            )

        # Extract session parameters
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_chooses_name] Retrieved session parameters: %s", session_parameters)

        # Step 2: Retrieve the current name
        current_name = session_parameters.get('person', 'unknown')
        if current_name == 'unknown':
            # Prompt the user to provide their name if it's missing
            logging.warning("[handle_user_chooses_name] Current name is missing or unknown.")
            current_name_message = (
                "It seems your current name is not on record. What name should I update it to?"
            )
        else:
            # Inform the user of their current name and prompt for an update
            current_name_message = f"Your current name is {current_name}. What would you like to update it to?"

        # Step 3: Build updated contexts
        output_contexts = build_contexts(session, 'await-name-update', session_parameters)

        # Step 4: Build response
        response_data = format_dialogflow_response(
            [current_name_message],
            output_contexts
        )
        logging.info("[handle_user_chooses_name] Response data prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_chooses_name] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_chooses_name] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )



#------------------------------------------------------------------------------------------
#RESPONSE FOR USER CHOOSES EMAIL FOR UPGRADE


def handle_user_chooses_email(body: dict) -> dict:
    """
    Handles the scenario where the user chooses to update their email.

    Purpose:
    --------
    - Extracts session details and current email from the Dialogflow webhook payload.
    - Prompts the user to confirm or provide the updated email.
    - Prepares the response and updated contexts for Dialogflow to handle the next step.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing session data, user inputs, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user to update their email.

    Steps:
    ------
    1. Extract the session ID and validate the output contexts.
    2. Retrieve the current email from session parameters.
    3. Prompt the user to provide a new email if the current email is missing or unknown.
    4. Update the contexts to guide Dialogflow to the next step (await-email-update).

    Error Handling:
    ---------------
    - Handles missing or invalid session details gracefully.
    - Logs and responds to unexpected runtime errors with a user-friendly error message.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """


    try:
        logging.info("[handle_user_chooses_email] Entering function.")

        # Step 1: Extract session and validate output contexts
        session = extract_session(body)

        # Validate that outputContexts exists and is not empty
        output_contexts = extract_output_contexts(body)
        if not output_contexts:
            logging.warning("[handle_user_chooses_email] Missing or empty outputContexts in request.")
            return format_dialogflow_response(
                ["I couldn't retrieve the current information. Please try again."],
                []
            )

        # Extract session parameters
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_chooses_email] Retrieved session parameters: %s", session_parameters)

        # Step 2: Retrieve the current email
        current_email = session_parameters.get('email', 'unknown')
        if current_email == 'unknown':
            logging.warning("[handle_user_chooses_email] Current email is missing or unknown.")
            current_email_message = (
                "It seems your current email is not on record. What email should I update it to?"
            )
        else:
            current_email_message = f"Your current email is {current_email}. What would you like to update it to?"

        # Step 3: Build updated contexts
        output_contexts = build_contexts(session, 'await-email-update', session_parameters)

        # Step 4: Build response
        response_data = format_dialogflow_response(
            [current_email_message],
            output_contexts
        )
        logging.info("[handle_user_chooses_email] Response data prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_chooses_email] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_chooses_email] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )




#-------------------------------------
#USER CHOOSES DATE-TIME

def handle_user_chooses_date_time(body: dict) -> dict:
    """
    Handles the user's intent to update their date and time.

    Purpose:
    --------
    - Extracts session details and the current date-time from the Dialogflow webhook payload.
    - Prompts the user to confirm or provide the updated date and time.
    - Prepares the response and updated contexts for Dialogflow to handle the next step.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing session data, user inputs, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user to update their date-time.

    Steps:
    ------
    1. Extract the session ID and validate the output contexts.
    2. Retrieve the current date-time from session parameters.
    3. Prompt the user to provide a new date-time if the current one is missing or unknown.
    4. Update the contexts to guide Dialogflow to the next step (await-date-time-update).

    Error Handling:
    ---------------
    - Handles missing or invalid session details gracefully.
    - Logs and responds to unexpected runtime errors with a user-friendly error message.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        logging.info("[handle_user_chooses_date_time] Entering function.")

        # Step 1: Extract session and validate output contexts
        session = extract_session(body)

        # Validate that outputContexts exists and is not empty
        output_contexts = extract_output_contexts(body)
        if not output_contexts:
            logging.warning("[handle_user_chooses_date_time] Missing or empty outputContexts in request.")
            return format_dialogflow_response(
                ["I couldn't retrieve the current information. Please try again."],
                []
            )

        # Extract session parameters
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_chooses_date_time] Retrieved session parameters: %s", session_parameters)

        # Step 2: Retrieve the current date-time
        date_time_data = session_parameters.get('date_time', 'unknown')
        if isinstance(date_time_data, dict):
            current_date_time = date_time_data.get('date_time', 'unknown')
        else:
            current_date_time = date_time_data


        # Check if the current date-time is missing or invalid
        if not current_date_time or current_date_time == 'unknown':
            logging.warning("[handle_user_chooses_date_time] Current date-time is missing or unknown.")
            current_date_time_message = (
                "It seems your current date and time are not on record. What would you like to update it to?"
            )
        else:


            formatted_date_time = datetime.fromisoformat(current_date_time).strftime('%Y-%m-%d at %I:%M %p')
            current_date_time_message = (

               # f"Your current date-time is {current_date_time}. What would you like to update it to?"

                f"Your current date-time is {formatted_date_time}. What would you like to update it to?"

            )

        # Step 3: Build updated contexts to guide Dialogflow to the next step (await-date-time-update)
        output_contexts = build_contexts(session, 'await-date-time-update', session_parameters)

        # Step 4: Build response
        response_data = format_dialogflow_response(
            [current_date_time_message],
            output_contexts
        )
        logging.info("[handle_user_chooses_date_time] Response prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_chooses_date_time] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_chooses_date_time] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )


#-------------------------------------


def handle_user_chooses_note(body: dict) -> dict:

    """
    Handles the user's intent to update their note.

    Purpose:
    --------
    - Retrieves the current note from the session parameters.
    - Prompts the user to confirm or provide an updated note.
    - Prepares the response and updated contexts for Dialogflow.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing session data, user inputs, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user to update their note.

    Steps:
    ------
    1. Extract session ID and validate the output contexts.
    2. Retrieve the current note from session parameters.
    3. Prompt the user to update the note.
    4. Update the contexts to guide Dialogflow to the next step (await-note-update).

    Error Handling:
    ---------------
    - Handles missing or invalid session details gracefully.
    - Logs and responds to unexpected runtime errors with a user-friendly error message.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        logging.info("[handle_user_chooses_note] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        
        # Check if outputContexts is empty
        if not output_contexts:
            logging.warning("[handle_user_chooses_note] No output contexts provided in the request.")
            return format_dialogflow_response(
                ["Something went wrong. Please try again later."],
                []
            )

        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_chooses_note] Retrieved session parameters: %s", session_parameters)

        # Step 2: Retrieve the current note from session parameters
        current_note = session_parameters.get('note', 'No note provided')
        if not current_note:
            logging.warning("[handle_user_chooses_note] Current note is missing or not provided.")
            current_note = 'No note provided'

        # Step 3: Build updated contexts for the next step (await-note-update)
        output_contexts = build_contexts(session, 'await-note-update', session_parameters)

        # Step 4: Build response for Dialogflow
        response_data = format_dialogflow_response(
            [f"Your current note is: {current_note}. What would you like to update it to?"],
            output_contexts
        )
        logging.info("[handle_user_chooses_note] Response prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_chooses_note] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_chooses_note] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )


#------------------------------------------------------------------------------------------
#RESPONSE FOR USER UPDATES NAME
#SA VALIDACIOM

def handle_user_updates_name(body: dict) -> dict:
    """
    Handles the scenario where the user updates their name.

    Purpose:
    --------
    - Extracts and validates the new name provided by the user.
    - Updates the session parameters with the new name.
    - Confirms the update and provides the current session details to the user.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs, session data, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, confirming the name update and prompting for further changes.

    Steps:
    ------
    1. Extract session ID, output contexts, and session parameters.
    2. Retrieve and validate the new name provided by the user.
    3. Update the session parameters with the validated name.
    4. Build the response, including updated contexts and confirmation message.

    Error Handling:
    ---------------
    - Gracefully handles missing or invalid session data.
    - Returns user-friendly messages for validation or unexpected errors.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
        - `validate_name`
    """

    try:
        logging.info("[handle_user_updates_name] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_updates_name] Retrieved session parameters: %s", session_parameters)

        # Step 2: Extract the new name (person.original)
        new_name = body['queryResult']['parameters'].get('person.original', '').strip() or session_parameters.get('person.original', '').strip()
        logging.info("[handle_user_updates_name] New name extracted: '%s'", new_name)

        # Step 3: Validate the new name
        if not validate_name(new_name):
            logging.warning("[handle_user_updates_name] Invalid name detected: '%s'", new_name)
            response_data = format_dialogflow_response(
                ["Hmm, that doesn’t look like a valid name. Please avoid special characters or numbers."],
                [
                    {
                        'name': f'{session}/contexts/await-name-update',
                        'lifespanCount': 1  # Keep asking for a valid name
                    },
                    {
                        'name': f'{session}/contexts/session-parameters',
                        'lifespanCount': 99
                    }
                ]
            )
            return response_data

        # Step 4: Update the name in session parameters
        session_parameters['person'] = new_name
        session_parameters['person.original'] = new_name  # Ensure consistency with .original
        logging.info("[handle_user_updates_name] Updated session parameters: %s", session_parameters)

        # Step 5: Build updated contexts for the next step
        output_contexts = build_contexts(session, 'await-confirmation', session_parameters)


        response_data = format_rich_response_with_chips(
            [
                f"Your name has been updated to: {new_name}.\n\n"
                f"Here’s what I have now:\n"
                f"📋 Name: {session_parameters.get('person.original', 'unknown')}\n"
                f"📧 Email: {session_parameters.get('email.original', 'unknown')}\n"
                f"📅 Date/Time: {datetime.fromisoformat(session_parameters.get('date_time', 'unknown')).strftime('%Y-%m-%d %H:%M') if session_parameters.get('date_time', 'unknown') != 'unknown' else 'unknown'}\n"
                f"📝 Note: {session_parameters.get('note', 'No note provided')}\n\n"
                "Is there anything else you want to change?"
            ],
            chips=["Yes", "No"],
            output_contexts=output_contexts
        )
        logging.info("[handle_user_updates_name] Response prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_updates_name] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_updates_name] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )



#------------------------------------------------------------------------------------------
#RESPONSE FOR USER UPDATES EMAIL


def handle_user_updates_email(body: dict) -> dict:
    """
    Handles the scenario where the user updates their email address.

    Purpose:
    --------
    - Extracts and validates the new email address provided by the user.
    - Updates the session parameters with the new email.
    - Confirms the update and provides the current session details to the user.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs, session data, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, confirming the email update and prompting for further changes.

    Steps:
    ------
    1. Extract session ID, output contexts, and session parameters.
    2. Retrieve and validate the new email provided by the user.
    3. Update the session parameters with the validated email.
    4. Build the response, including updated contexts and confirmation message.

    Error Handling:
    ---------------
    - Gracefully handles missing or invalid session data.
    - Returns user-friendly messages for validation or unexpected errors.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
        - `is_valid_email`
    """

    try:
        logging.info("[handle_user_updates_email] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_updates_email] Retrieved session parameters: %s", session_parameters)

        # Step 2: Extract the new email
        new_email = body['queryResult']['parameters'].get('email.original', '').strip() or session_parameters.get('email.original', '').strip()
        logging.info("[handle_user_updates_email] New email extracted: '%s'", new_email)

        # Step 3: Validate the new email
        if not is_valid_email(new_email):
            logging.warning("[handle_user_updates_email] Invalid email detected: '%s'", new_email)
            response_data = format_dialogflow_response(
                ["Hmm, that doesn’t look like a valid email address. Could you try again?"],
                [
                    {
                        'name': f'{session}/contexts/await-email-update',
                        'lifespanCount': 1  # Keep asking for a valid email
                    },
                    {
                        'name': f'{session}/contexts/session-parameters',
                        'lifespanCount': 99
                    }
                ]
            )
            return response_data

        # Step 4: Update the email in session parameters
        session_parameters['email'] = new_email
        session_parameters['email.original'] = new_email  # Ensure consistency with .original
        logging.info("[handle_user_updates_email] Updated session parameters: %s", session_parameters)

        # Step 5: Build updated contexts for the next step
        output_contexts = build_contexts(session, 'await-confirmation', session_parameters)


        response_data = format_rich_response_with_chips(
          [
				f"Your email has been successfully updated to: {new_email}.\n\n"
				f"Here’s what I have now:\n"
				f"📋 Name: {session_parameters.get('person.original', 'unknown')}\n"
				f"📧 Email: {session_parameters.get('email.original', 'unknown')}\n"
				f"📅 Date/Time: {datetime.fromisoformat(session_parameters.get('date_time', 'unknown')).strftime('%Y-%m-%d %H:%M') if session_parameters.get('date_time', 'unknown') != 'unknown' else 'unknown'}\n"
				f"📝 Note: {session_parameters.get('note', 'No note provided')}\n\n"
				"Is there anything else you want to change?"
           ],         

            chips=["Yes", "No"],
            output_contexts=output_contexts
        )
        logging.info("[handle_user_updates_email] Response prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_updates_email] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )

    except Exception as e:
        logging.error("[handle_user_updates_email] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )

#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------
#RESPONSE FOR USER WANTS TO UPDATES DATE-TIME 




def handle_user_updates_date_time(body: dict) -> dict:
    """
    Handles the scenario where the user updates the date and time for an appointment.

    Purpose:
    --------
    - Validates the user's new date-time input.
    - Converts the date-time to UTC and updates session parameters.
    - Checks for slot availability and suggests alternatives if necessary.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs, session data, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, confirming or suggesting updates to the date and time.

    Steps:
    ------
    1. Extract session ID, output contexts, and session parameters.
    2. Validate the new date-time provided by the user.
    3. Convert the valid date-time to UTC and update session parameters.
    4. Check the availability of the requested slot.
    5. Provide feedback to the user, including suggested alternatives if the requested time is unavailable.

    Error Handling:
    ---------------
    - Returns user-friendly error messages for invalid inputs or unexpected issues.
    - Handles date-time validation, UTC conversion, and slot availability errors gracefully.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `convert_to_utc_and_store`
        - `find_available_slot`
        - `format_dialogflow_response`
        - `format_rich_response_with_chips`
        - `build_contexts`
    """

    try:
        logging.info("[handle_user_updates_date_time] Entering function.")

        # Step 1: Extract session, output contexts, and session parameters
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_updates_date_time] Session parameters: %s", session_parameters)

        # Step 2: Extract and validate date-time input
        is_valid, date_time_value = extract_and_validate_date_time(body, 'await-date-time-update', session_parameters)
        if not is_valid:
            logging.warning("[handle_user_updates_date_time] Invalid date-time input: %s", date_time_value)
            return format_dialogflow_response(
                ["I didn’t catch that. Can you provide a date and time like 'Tomorrow at 1 pm'?"],
                build_contexts(session, 'await-date-time-update', session_parameters)
            )


            # Step 3: Past Date Validation
            # Parse the provided date-time value into a datetime object

            parsed_date_time = datetime.fromisoformat(date_time_value)


            # Validate and normalize the timezone
            user_timezone = session_parameters.get("timezone", "UTC")  # Default to UTC if missing
            if not user_timezone or user_timezone not in pytz.all_timezones:
                logging.warning(f"[handle_user_updates_date_time] Invalid or missing timezone '{user_timezone}'. Falling back to UTC.")
                user_timezone = "UTC"

            # Ensure both times are timezone-aware

            current_time = datetime.now(pytz.timezone(user_timezone))  # Current time in user's timezone

            parsed_date_time = parsed_date_time.astimezone(pytz.timezone(user_timezone))  # Adjust parsed date-time to user's timezone

            # Compare the parsed date-time with the current time

            if parsed_date_time < current_time:
                logging.warning(f"[handle_user_updates_date_time] The requested date-time {parsed_date_time} is in the past.")

                return format_dialogflow_response(
                        ["You can’t schedule for a past date or time. Please choose a future date and time."],
                        build_contexts(session, 'await-date-time-update', session_parameters)
                        )


        # NEW: Step 3 - Validate working hours
        user_timezone = session_parameters.get("timezone", "Europe/Belgrade")
        if not user_timezone:  # If timezone is empty, fallback to the default
            logging.warning("[handle_user_updates_date_time] Timezone is empty. Defaulting to Europe/Belgrade.")
            user_timezone = "Europe/Belgrade"

        # Use the date_time_value with working hours validation
        if not is_within_working_hours(date_time_value, timezone=user_timezone):
            logging.warning(f"[handle_user_updates_date_time] Time {date_time_value} is outside working hours.")
            return format_dialogflow_response(
                [f"Sorry, that time is outside our working hours ({WORKING_HOURS['start']}:00 to {WORKING_HOURS['end']}:00). Please provide another time."],
                build_contexts(session, 'await-date-time-update', session_parameters)
            )



        # Step 3: Convert the date-time to UTC and update session parameters
        try:
            session_parameters = convert_to_utc_and_store(
                date_time_value, session_parameters, timezone=session_parameters.get('timezone', 'UTC')
            )
        except ValueError as e:
            logging.error("[handle_user_updates_date_time] Error in date-time conversion: %s", e, exc_info=True)
            return format_dialogflow_response(
                ["The date-time format is invalid. Please provide it in a valid format like 'Tomorrow at 1 pm'."],
                build_contexts(session, 'await-date-time-update', session_parameters)
            )

        # Step 4: Find an available slot for the updated date-time

        try:
            is_slot_found, slot_details = find_available_slot(
                session_parameters['date_time'], session_parameters['timezone'], max_attempts=12
            )
            logging.info("[handle_user_updates_date_time] Slot search result: %s", slot_details)
        except Exception as e:
            logging.error("[handle_user_updates_date_time] Error finding available slot: %s", e, exc_info=True)
            return format_dialogflow_response(
                ["An error occurred while checking availability. Please try again later."],
                build_contexts(session, 'await-date-time-update', session_parameters)
            )

        # Step 5: Handle slot availability results
        if is_slot_found:   # If a slot is found
            session_parameters['date_time'] = slot_details['local_time'].isoformat()
            session_parameters['utc_time'] = slot_details['utc_time']

            if slot_details['is_original']: # If the requested time is available
                output_contexts = build_contexts(session, 'await-confirmation', session_parameters)
                formatted_date_time = datetime.fromisoformat(date_time_value).strftime('%Y-%m-%d at %I:%M %p')  # Example: 2025-01-29 at 11:00 AM
                return format_rich_response_with_chips(
                    [
                       # f"Great! The time you selected ({date_time_value}) is available. Here’s what I have now:\n"
                        f"Great! The time you selected {formatted_date_time} is available. Here’s what I have now:\n\n"

                        f"- Name: {session_parameters.get('person', 'unknown')}\n"
                        f"- Email: {session_parameters.get('email', 'unknown')}\n"
                        #f"- Date/Time: {date_time_value}\n"
                        f"Date/Time: {formatted_date_time}\n"

                        f"- Note: {session_parameters.get('note', 'No note provided')}\n"
                        "Is there anything else you would like to change?"
                    ],
                    chips=["Yes", "No"],
                    output_contexts=output_contexts
                )
            else:   # Suggest an alternative time slot
                suggested_local_time = slot_details['local_time'].strftime('%Y-%m-%d %H:%M %Z')
                output_contexts = build_contexts(session, 'await-slot-confirmation-update', session_parameters)


                formatted_requested_time = datetime.fromisoformat(date_time_value).strftime('%Y-%m-%d at %I:%M %p')  # Example: 2025-01-29 at 10:00 AM
                formatted_suggested_time = slot_details['local_time'].strftime('%Y-%m-%d at %I:%M %p')  # Example: 2025-01-29 at 11:00 AM





                return format_rich_response_with_chips(
                    [

                        f"Unfortunately, the time you requested (**{formatted_requested_time}**) is unavailable.",
                        f"However, the following slot is available:",
                        f"**Date/Time**: {formatted_suggested_time}",
                    "Would you like to schedule this time?"
                    ],
                    chips=["Yes", "No"],
                    output_contexts=output_contexts
                )

        # Step 6: Handle the case where no slots are available
        logging.warning("[handle_user_updates_date_time] No slots available.")
        return format_dialogflow_response(
            ["I'm sorry, no slots are available within the next 6 hours. Please provide another time."],
            build_contexts(session, 'await-date-time-update', session_parameters)
        )

    except ValueError as ve:
        logging.warning("[handle_user_updates_date_time] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )
    except Exception as e:
        logging.error("[handle_user_updates_date_time] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )



#------------------------------------------------------------------------------------------
#USER CONFIRMS SLOT UPDATE

#NISI TESTIRAO
def handle_user_confirms_slot_update(body: dict) -> dict:
    """
    Handles the scenario where the user confirms an updated date-time slot for an appointment.

    Purpose:
    --------
    - Confirms the updated date-time slot selected by the user.
    - Updates the session parameters with the confirmed date-time.
    - Provides a summary of the appointment details for user review.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs, session data, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, summarizing the updated appointment details and 
            prompting the user for further updates if necessary.

    Steps:
    ------
    1. Extract session ID, output contexts, and session parameters.
    2. Validate the updated date-time and store it as confirmed in session parameters.
    3. Build response contexts for the next step.
    4. Provide a summary of the updated details, with options for further updates.

    Error Handling:
    ---------------
    - Returns user-friendly error messages for missing or invalid date-time input.
    - Handles unexpected runtime errors gracefully.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_rich_response_with_chips`
        - `format_dialogflow_response`
    """

    try:
        logging.info("[handle_user_confirms_slot_update] Entering function.")

        # Step 1: Extract session, output contexts, and session parameters
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_confirms_slot_update] Session parameters: %s", session_parameters)

        # Step 2: Confirm the updated date-time
        confirmed_date_time = session_parameters.get('date_time', 'unknown')  # Fetch the updated date-time
        if confirmed_date_time == 'unknown':
            logging.warning("[handle_user_confirms_slot_update] Date-time is missing or unknown.")
            return format_dialogflow_response(
                ["Something went wrong while confirming the updated date-time. Please try again."],
                build_contexts(session, 'await-date-time-update', session_parameters)
            )

        # Update the confirmed date-time in session parameters
        session_parameters['confirmed_date_time'] = confirmed_date_time  # Store the confirmation
        logging.info("[handle_user_confirms_slot_update] Confirmed date-time: %s", confirmed_date_time)

        # Step 3: Build updated contexts for the next step
        output_contexts = build_contexts(session, 'await-confirmation', session_parameters)

        # Step 4: Build response summarizing updated details
        response_data = format_rich_response_with_chips(
            [
                #f"Your date has been updated to {confirmed_date_time}. Here’s what I have now:\n"
                f"Your appointment has been successfully updated! 🎉\n\n"
                f"- Name: {session_parameters.get('person', 'unknown')}\n"
                f"- Email: {session_parameters.get('email', 'unknown')}\n"
#                f"- Date/Time: {confirmed_date_time}\n"

                f"**Date/Time**: {datetime.fromisoformat(confirmed_date_time).strftime('%Y-%m-%d at %I:%M %p')}\n"

                f"- Note: {session_parameters.get('note', 'No note provided')}\n"
                "Is there anything else you would like to change?"
            ],
            chips=["Yes", "No"],
            output_contexts=output_contexts
        )

        logging.info("[handle_user_confirms_slot_update] Response data: %s", response_data)
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_confirms_slot_update] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )
    except Exception as e:
        logging.error("[handle_user_confirms_slot_update] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )



#-----------------------------------------------------------------------------------------
#USER DENIES SLOT UPDATE
#NOVOOOOOOO:wq

#NISI TESTIRAO
def handle_user_denies_slot_update(body: dict) -> dict:
    """
    Handles the scenario where the user denies the suggested updated date-time slot.

    Purpose:
    --------
    - Resets the context to allow the user to provide a new date and time for their appointment.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs, session data, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, prompting the user to provide a new date and time.

    Steps:
    ------
    1. Extract session ID, output contexts, and session parameters.
    2. Reset the context to 'await-date-time-update' for capturing new date-time input.
    3. Prompt the user to provide a new date and time.

    Error Handling:
    ---------------
    - Returns user-friendly error messages for invalid session data or missing contexts.
    - Handles unexpected runtime errors gracefully.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_dialogflow_response`
    """

    try:
        logging.info("[handle_user_denies_slot_update] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_denies_slot_update] Session parameters: %s", session_parameters)

        # Step 2: Reset contexts for a new date-time update
        output_contexts = build_contexts(session, 'await-date-time-update', session_parameters)
        logging.info("[handle_user_denies_slot_update] Updated contexts for new date-time: %s", output_contexts)

        # Step 3: Build the response
        response_data = format_dialogflow_response(
            [
                "No problem! Please provide a new date and time for your appointment, like 'Tomorrow at 1 pm.'"
            ],
            output_contexts
        )
        logging.info("[handle_user_denies_slot_update] Response data: %s", response_data)
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_denies_slot_update] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )
    except Exception as e:
        logging.error("[handle_user_denies_slot_update] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )





#------------------------------------------------------------------------------------------


#RESPONSE FOR USER WANTS TO UPDATES NOTEe


#nisi testirao
def handle_user_updates_note(body: dict) -> dict:
    """
    Handles the scenario where the user provides an updated note.

    Purpose:
    --------
    - Prompts the user to confirm or re-enter their note.
    - Updates session parameters with the new note.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs, session data, and contexts.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, confirming the note update and prompting for additional changes.

    Steps:
    ------
    1. Extract session ID, output contexts, and session parameters.
    2. Extract and validate the new note.
    3. Update session parameters with the new note.
    4. Build response to confirm the note update and display current session information.

    Error Handling:
    ---------------
    - Prompts the user again if no note is provided.
    - Handles invalid session data or unexpected runtime errors gracefully.

    Dependencies:
    --------------
    - Utility functions:
        - `extract_session`
        - `extract_output_contexts`
        - `extract_session_parameters`
        - `build_contexts`
        - `format_rich_response_with_chips`
    """

    try:
        logging.info("[handle_user_updates_note] Entering function.")

        # Step 1: Extract session and output contexts
        session = extract_session(body)
        output_contexts = extract_output_contexts(body)
        session_parameters = extract_session_parameters(output_contexts)
        logging.info("[handle_user_updates_note] Session parameters: %s", session_parameters)

        # Step 2: Extract the new note
        new_note = body['queryResult']['parameters'].get('any', '').strip()
        if not new_note:
            # If the note is missing or invalid, prompt the user to provide it again
            logging.warning("[handle_user_updates_note] No note provided.")
            return format_dialogflow_response(
                ["I didn’t catch that. Please provide a valid note."],
                [
                    {
                        'name': f'{session}/contexts/await-note-update',
                        'lifespanCount': 1  # Re-prompt for valid note
                    },
                    {
                        'name': f'{session}/contexts/session-parameters',
                        'lifespanCount': 99,
                        'parameters': session_parameters  # Preserve session data
                    }
                ]
            )

        # Step 3: Update the note in session parameters
        session_parameters['note'] = new_note
        logging.info("[handle_user_updates_note] Note updated to: %s", new_note)


        # Step 4: Format the Date/Time field into a readable format
        date_time = session_parameters.get('date_time', 'unknown')
        if date_time != "unknown":
            try:
                # Format date-time to "2025-01-29 10:00 h"
                date_time = datetime.fromisoformat(date_time).strftime("%Y-%m-%d %H:%M h")
            except ValueError:
                logging.warning("[handle_user_updates_note] Invalid date_time format, using raw value.")


        # Step 4: Build updated contexts
        output_contexts = build_contexts(session, 'await-confirmation', session_parameters)

        # Step 5: Build response with Yes/No chips
        response_data = format_rich_response_with_chips(
            [
                f"Your note has been updated to: {new_note}. Here’s what I have now:\n"
                f"- Name: {session_parameters.get('person', 'unknown')}\n"
                f"- Email: {session_parameters.get('email', 'unknown')}\n"
                f"📅 Date/Time: {date_time}\n"
               # f"- Date/Time: {session_parameters.get('date_time', 'unknown')}\n"
                f"- Note: {new_note}\n"
                "Is there anything else you want to change?"
            ],
            chips=["Yes", "No"],
            output_contexts=output_contexts
        )
        logging.info("[handle_user_updates_note] Response data: %s", response_data)
        return response_data


    except ValueError as ve:
        logging.warning("[handle_user_updates_note] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again."],
            []
        )
    except Exception as e:
        logging.error("[handle_user_updates_note] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )


#------------------------------------------------------------------------------------------


#------------------------------------------------------------------------------------------


import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
from utils.helper_functions import get_system_message
load_dotenv()
import json


# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def handle_fallback_intent(body: dict) -> dict:
    """
    Handles fallback scenarios in Dialogflow by responding based on the detected active context
    or leveraging OpenAI GPT to generate dynamic responses when no context is active.

    Purpose:
    --------
    This function manages user queries that don't match a specific intent in Dialogflow. It first checks for active
    contexts in the Dialogflow request and provides tailored responses. If no context is active, the function uses
    OpenAI GPT to generate an appropriate reply dynamically.

    Parameters:
    ------------
    - body (dict): The request body from Dialogflow, containing the query, session, and context details.

    Returns:
    ---------
    - dict: A response formatted for Dialogflow, including a text message and updated output contexts.

    Steps:
    ------
    1. Extract session and validate the request body.
    2. Detect active contexts (if any).
    3. Provide context-specific responses or generate a dynamic fallback response using OpenAI GPT.
    4. Build and return the response for Dialogflow.

    Error Handling:
    ---------------
    - Logs all steps and errors for debugging.
    - Returns generic error messages for unexpected failures.

    Dependencies:
    --------------
    - Requires OpenAI GPT API for dynamic responses.
    - Utilizes utility functions like `extract_session`, `extract_output_contexts`, and `get_system_message`.
    """

    try:

        # Step 1: Extract session from the Dialogflow request
        session = extract_session(body)
        logging.info("[handle_fallback_intent] Extracted session: %s", session)
        
        # Step 2: Extract output contexts for identifying active contexts
        output_contexts = extract_output_contexts(body)
        logging.info("[handle_fallback_intent] Extracted output contexts: %s", output_contexts)
        
        # Step 3: Detect the active context from the request
        active_context = None
        for context in output_contexts:
            if 'await-name-update' in context['name']:
                active_context = 'await-name-update'
                break
            elif 'await-email-update' in context['name']:
                active_context = 'await-email-update'
                break
            elif 'await-date-time-update' in context['name']:
                active_context = 'await-date-time-update'
                break
            elif 'await-slot-confirmation-update' in context['name']:
                active_context = 'await-slot-confirmation-update'
                break
            elif 'await-note-update' in context['name']:
                active_context = 'await-note-update'
                break
            elif 'await-date-time' in context['name']:
                active_context = 'await-date-time'
                break
            elif 'await-slot-confirmation' in context['name']:
                active_context = 'await-slot-confirmation'
                break
            elif 'await-name' in context['name']:
                active_context = 'await-name'
                break
            elif 'await-email' in context['name']:
                active_context = 'await-email'
                break
            elif 'await-confirmation' in context['name']:
                active_context = 'await-confirmation'
                break
            elif 'await-field' in context['name']:
                active_context = 'await-field'
                break
            elif 'await-note-action' in context['name']:
                active_context = 'await-note-action'
                break

        logging.info("[handle_fallback_intent] Detected active context: %s", active_context)

        # Step 4: Respond based on active context
        if active_context:
            if active_context == 'await-name-update':
                message = "I still need your updated name. What would you like to change it to?"
            elif active_context == 'await-email-update':
                message = "I still need your updated email. Could you provide it again?"
            elif active_context == 'await-date-time-update':
                message = "I didn’t catch that. Can you provide a date and time like 'Tomorrow at 1 pm'?"
            elif active_context == 'await-slot-confirmation-update':
                message = "I didn’t catch that. Do you want to confirm this time slot? Please say 'yes' or 'no.'"
            elif active_context == 'await-note-update':
                message = "I didn’t understand your note. Please provide the note you'd like to add."
            elif active_context == 'await-name':
                message = "Sorry, I didn’t get that. Can you provide your name?"
            elif active_context == 'await-email':
                message = "Sorry, I didn’t get that. Can you provide your email?"
            elif active_context == 'await-confirmation':
                message = "If you want to update something, just say 'Yes.' If everything looks good, say 'No.'"
            elif active_context == 'await-field':
                message = "What would you like to update? Your name, email, date-time, or note?"
            elif active_context == 'await-date-time':
                message = "I didn’t understand the date and time. Please provide it in this format: 'Tomorrow at 1 pm'."
            elif active_context == 'await-slot-confirmation':
                message = "I didn’t catch that. Do you want to confirm this time slot? Please say 'yes' or 'no.'"
            elif active_context == 'await-note-action':
                message = "I didn’t catch that. Please say 'yes' if you want to add a note or 'no' if you don’t."

            # Update the context lifespan to keep it active
            updated_contexts = [{'name': f'{session}/contexts/{active_context}', 'lifespanCount': 1}]
        else:
            # Step 5: No active context found, use OpenAI GPT for dynamic fallback responses
            logging.info("[handle_fallback_intent] No active context found. Using OpenAI fallback.")
            try:
                user_query = body['queryResult'].get('queryText', '').strip()
                system_message = get_system_message()

                # Define user message
                user_message = {"role": "user", "content": user_query}

                # Call GPT API
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[system_message, user_message],
                    temperature=0.6,
                    max_tokens=500,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0.6
                )

                # Extract GPT response
                message = response.choices[0].message.content
                logging.info("[handle_fallback_intent] GPT response: %s", message)
            except Exception as e:
                logging.error("[handle_fallback_intent] Error with OpenAI API: %s", e, exc_info=True)
                message = "I'm sorry, but I couldn’t process your request. Please try again later."

            updated_contexts = []

        # Step 6: Build the response to send back to Dialogflow
        response_data = {
            "fulfillmentMessages": [{"text": {"text": [message]}}],
            "outputContexts": updated_contexts
        }
        logging.info("[handle_fallback_intent] Constructed response: %s", response_data)

        return response_data

    except Exception as e:
        logging.error("[handle_fallback_intent] Unexpected error occurred: %s", e, exc_info=True)
        return {
            "fulfillmentMessages": [{"text": {"text": ["An error occurred. Please try again later."]}}]
        }




#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#PRODUCTS



def handle_user_wants_products(body: dict) -> dict:
    """
    Handles the user's request to view available products.

    Purpose:
    --------
    - Provides a list of available products for the user to choose from.
    - Sets an output context to track that the user is viewing the product list.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs and session details.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, listing the available products and providing options for user selection.

    Steps:
    ------
    1. Extract the session ID from the request body.
    2. Set the output context for product selection tracking.
    3. Format the response to include the list of products and quick reply options.

    Error Handling:
    ---------------
    - Logs and handles cases where the session is missing or invalid.
    - Gracefully handles unexpected runtime errors.

    Dependencies:
    --------------
    - Utility functions:
        - `format_rich_response_with_chips`
    """

    try:
        logging.info("[handle_user_wants_products] Entering function.")
        
        # Step 1: Extract session from the incoming body
        session = body.get('session')
        if not session:
            logging.warning("[handle_user_wants_products] Missing session in the request body.")
            raise ValueError("Missing session in the request body.")

        logging.info("[handle_user_wants_products] Extracted session: %s", session)

        # Step 2: Set the output context
        output_contexts = [
            {
                "name": f"{session}/contexts/await-product-list",
                "lifespanCount": 1
            }
        ]
        logging.info("[handle_user_wants_products] Set output context: %s", output_contexts)

        # Step 3: Format the response
        response_data = format_rich_response_with_chips(
            [




                "✨ **Our Product Range**",
                "",
                "1️⃣ **Tea Tree Shampoo**\nRefreshes and cleanses your scalp, leaving it invigorated.",
                "",
                "2️⃣ **Shampoo One**\nA gentle shampoo, perfect for everyday use.",
                "",
                "3️⃣ **Double Hitter**\nA convenient shampoo-and-conditioner combo for your busy schedule.",
                "",
                "💡 **Select a product to learn more!**",



            ],
            chips=['Tea Tree Shampoo', 'Shampoo One', 'Double Hitter', 'Restart Chat'],
            output_contexts=output_contexts
        )
        logging.info("[handle_user_wants_products] Response data: %s", response_data)

        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_wants_products] ValueError: %s", ve)
        return format_dialogflow_response(
            ["Something went wrong while processing your request. Please try again later."],
            []
        )
    except Exception as e:
        logging.error("[handle_user_wants_products] Unexpected error occurred: %s", e, exc_info=True)
        return format_dialogflow_response(
            ["An unexpected error occurred. Please try again later."],
            []
        )



#-----------------------------------------------------------------------------------------------



def handle_user_wants_tea_tree_shampoo(body: dict) -> dict:

    """
    Handles the user's request for details about the Tea Tree Special Shampoo.

    Purpose:
    --------
    - Provides product details, including a description, key benefits, usage instructions, and availability.
    - Includes a "Buy Now" link and quick navigation options.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs and session details.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, featuring rich content with product details and actionable options.

    Steps:
    ------
    1. Extract the session ID from the request body.
    2. Set the output context to track that the user is viewing Tea Tree Shampoo details.
    3. Build a response with rich content, including images, a description, benefits, and navigation options.

    Error Handling:
    ---------------
    - Handles cases where session data is missing or invalid.
    - Logs unexpected runtime errors and provides user-friendly error messages.

    Dependencies:
    --------------
    - Static file path for product image: `http://localhost:5000/static/tea-tree-shampoo.jpg`.
    - External link for purchasing the product: `https://example.com/tea_tree_shampoo`.
    """

    try:
        logging.info("[handle_user_wants_tea_tree_shampoo] Entering function.")

        # Step 1: Extract session from the incoming body
        session = extract_session(body)

        # Step 2: Set output contexts
        output_contexts = [
            {
                "name": f"{session}/contexts/await-tea-tree-shampoo",
                "lifespanCount": 1
            }
        ]

        # Step 3: Build the rich content response
        response_data = {
            "fulfillmentMessages": [
                {
                    "payload": {
                        "richContent": [
                            [
                                # Product Image
                                {
                                    "type": "image",
                                    "rawUrl": "https://bot-salona-f40de31fc167.herokuapp.com/static/tea-tree-shampoo.jpg",

                                    "accessibilityText": "Paul Mitchell Tea Tree Special Shampoo"
                                },
                                # Product Description
                                {
                                    "type": "description",
                                    "title": "Paul Mitchell Tea Tree Special Shampoo",
                                    "text": [
                                        "**Description**: An invigorating cleanser that washes away impurities, leaving the scalp feeling fresh and clean.",
                                        "**Key Benefits**:",
                                        "- Deep cleanses the scalp and hair.",
                                        "- Provides an invigorating sensation.",
                                        "- Leaves hair full of vitality and luster.",
                                        "**Usage Instructions**: Apply a small amount to damp hair. Lather and massage into the scalp for a few minutes. Rinse thoroughly. Suitable for all hair types.",
                                        "**Availability**: Available at Supercuts salons and authorized retailers."
                                    ]
                                },
                                # Buy Now Button
                                {
                                    "type": "button",
                                    "icon": {
                                        "type": "chevron_right",
                                        "color": "#FF5733"
                                    },
                                    "text": "Buy Now",
                                    "link": "https://example.com/tea_tree_shampoo"
                                },
                                # Chips for Navigation
                                {
                                    "type": "chips",
                                    "options": [
                                        {"text": "View Other Products"},
                                        {"text": "Schedule Appointment"},
                                        {"text": "Restart Chat"}
                                    ]
                                }
                            ]
                        ]
                    }
                }
            ],
            "outputContexts": output_contexts
        }

        logging.info("[handle_user_wants_tea_tree_shampoo] Response data prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_wants_tea_tree_shampoo] ValueError: %s", ve)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong while processing your request. Please try again."]}}
            ]
        }

    except Exception as e:
        logging.error("[handle_user_wants_tea_tree_shampoo] Unexpected error occurred: %s", e, exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }



#-----------------------------------------------------------------------------------------------



def handle_user_wants_shampoo_one(body: dict) -> dict:
    """
    Handles the user's request for details about Paul Mitchell Shampoo One.

    Purpose:
    --------
    - Provides detailed product information, including description, benefits, usage instructions, and availability.
    - Includes actionable options such as a "Buy Now" button and quick navigation chips.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs and session details.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, featuring rich content with product details and actionable options.

    Steps:
    ------
    1. Extract the session ID from the request body.
    2. Set the output context for tracking that the user is viewing Shampoo One details.
    3. Build a response with rich content, including images, a description, benefits, and navigation options.

    Error Handling:
    ---------------
    - Handles cases where session data is missing or invalid.
    - Logs unexpected runtime errors and provides user-friendly error messages.

    Dependencies:
    --------------
    - Static file path for product image: `http://localhost:5000/static/shampoo-one.jpg`.
    - External link for purchasing the product: `https://example.com/shampoo_one`.
    """



    try:
        logging.info("[handle_user_wants_shampoo_one] Entering function.")

        # Step 1: Extract session from the incoming body
        session = extract_session(body)
        logging.info("[handle_user_wants_shampoo_one] Extracted session: %s", session)

        # Step 2: Set output contexts
        output_contexts = [
            {
                "name": f"{session}/contexts/await-one-shampoo",
                "lifespanCount": 1
            }
        ]

        # Step 3: Build the rich content response
        response_data = {
            "fulfillmentMessages": [
                {
                    "payload": {
                        "richContent": [
                            [
                                # Product Image
                                {
                                    "type": "image",
                                    "rawUrl": "https://bot-salona-f40de31fc167.herokuapp.com/static/shampoo-one.jpg",  
                                    "accessibilityText": "Paul Mitchell Shampoo One"
                                },
                                # Product Description
                                {
                                    "type": "description",
                                    "title": "Paul Mitchell Shampoo One",
                                    "text": [
                                        "**Description**: A gentle shampoo designed to cleanse hair without stripping away essential moisture. Ideal for color-treated, fine, and medium hair types, it enhances manageability and adds deep shine.",
                                        "**Key Benefits**:",
                                        "- Gently cleanses and improves manageability.",
                                        "- Adds deep shine.",
                                        "- Suitable for color-treated hair.",
                                        "**Usage Instructions**: Apply a small amount to wet hair. Lather and rinse completely. Gentle enough for daily use.",
                                        "**Availability**: Available at Supercuts salons and authorized retailers."
                                    ]
                                },
                                # Buy Now Button
                                {
                                    "type": "button",
                                    "icon": {
                                        "type": "chevron_right",
                                        "color": "#FF5733"
                                    },
                                    "text": "Buy Now",
                                    "link": "https://example.com/shampoo_one"
                                },
                                # Chips for Navigation
                                {
                                    "type": "chips",
                                    "options": [
                                        {"text": "View Other Products"},
                                        {"text": "Schedule Appointment"},
                                        {"text": "Restart Chat"}
                                    ]
                                }
                            ]
                        ]
                    }
                }
            ],
            "outputContexts": output_contexts
        }

        logging.info("[handle_user_wants_shampoo_one] Response data prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_wants_shampoo_one] ValueError: %s", ve)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong while processing your request. Please try again."]}}
            ]
        }

    except Exception as e:
        logging.error("[handle_user_wants_shampoo_one] Unexpected error occurred: %s", e, exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }




#-----------------------------------------------------------------------------------------------


def handle_user_wants_double_hitter_shampoo(body: dict) -> dict:
    """
    Handles the user's request for details about the MITCH by Paul Mitchell Double Hitter 2-in-1 Shampoo & Conditioner.

    Purpose:
    --------
    - Provides detailed product information, including a description, benefits, usage instructions, and availability.
    - Includes actionable options such as a "Buy Now" button and quick navigation chips.

    Parameters:
    ------------
    - body (dict): Dialogflow webhook request payload containing user inputs and session details.

    Returns:
    ---------
    - dict: A structured response formatted for Dialogflow, featuring rich content with product details and actionable options.

    Steps:
    ------
    1. Extract the session ID from the request body.
    2. Set the output context for tracking that the user is viewing Double Hitter Shampoo details.
    3. Build a response with rich content, including images, a description, benefits, and navigation options.

    Error Handling:
    ---------------
    - Handles cases where session data is missing or invalid.
    - Logs unexpected runtime errors and provides user-friendly error messages.

    Dependencies:
    --------------
    - Static file path for product image: `http://localhost:5000/static/double-hitter.jpg`.
    - External link for purchasing the product: `https://example.com/double_hitter`.
    """
    try:
        logging.info("[handle_user_wants_double_hitter_shampoo] Entering function.")

        # Step 1: Extract session using the utility function
        session = extract_session(body)
        logging.info("[handle_user_wants_double_hitter_shampoo] Extracted session: %s", session)

        # Step 2: Set output contexts
        output_contexts = [
            {
                "name": f"{session}/contexts/await-double-hitter-shampoo",
                "lifespanCount":1 
            }
        ]

        # Step 3: Build the rich content response
        response_data = {
            "fulfillmentMessages": [
                {
                    "payload": {
                        "richContent": [
                            [
                                # Product Image
                                {
                                    "type": "image",
                                    "rawUrl": "https://bot-salona-f40de31fc167.herokuapp.com/static/double-hitter.jpg",  # Update image path if needed

                                    "accessibilityText": "MITCH by Paul Mitchell Double Hitter 2-in-1 Shampoo & Conditioner"
                                },
                                # Product Description
                                {
                                    "type": "description",
                                    "title": "MITCH by Paul Mitchell Double Hitter 2-in-1 Shampoo & Conditioner",
                                    "text": [
                                        "**Description**: A sulfate-free formula that combines shampoo and conditioner in one step. It cleanses and conditions, leaving hair full and healthy-looking. Suitable for all hair types, especially fine to medium hair.",
                                        "**Key Benefits**:",
                                        "- Cleanses and conditions in one step.",
                                        "- Leaves hair with a healthy appearance.",
                                        "- Sulfate-free formula.",
                                        "**Usage Instructions**: Lather into damp hair and rinse. Ideal for daily use.",
                                        "**Availability**: Available at Supercuts salons and authorized retailers."
                                    ]
                                },
                                # Buy Now Button
                                {
                                    "type": "button",
                                    "icon": {
                                        "type": "chevron_right",
                                        "color": "#FF5733"
                                    },
                                    "text": "Buy Now",
                                    "link": "https://example.com/double_hitter"
                                },
                                # Chips for Navigation
                                {
                                    "type": "chips",
                                    "options": [
                                        {"text": "View Other Products"},
                                        {"text": "Schedule Appointment"},
                                        {"text": "Restart Chat"}
                                    ]
                                }
                            ]
                        ]
                    }
                }
            ],
            "outputContexts": output_contexts
        }

        logging.info("[handle_user_wants_double_hitter_shampoo] Response data prepared successfully.")
        return response_data

    except ValueError as ve:
        logging.warning("[handle_user_wants_double_hitter_shampoo] ValueError: %s", ve)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["Something went wrong while processing your request. Please try again."]}}
            ]
        }

    except Exception as e:
        logging.error("[handle_user_wants_double_hitter_shampoo] Unexpected error occurred: %s", e, exc_info=True)
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["An unexpected error occurred. Please try again later."]}}
            ]
        }





