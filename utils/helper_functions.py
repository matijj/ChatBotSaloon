"""
helper_functions.py

This module contains utility functions for use in Dialogflow webhook integration.
These functions handle tasks such as:
- Formatting responses for Dialogflow's fulfillment API.
- Extracting session and context data from Dialogflow requests.
- Validating user-provided inputs (e.g., email addresses, names).
- Building output contexts to guide Dialogflow's conversational flow.
- Generating rich responses with chips, images, and more.

Key Features:
1. **Response Formatting**:
    - `format_dialogflow_response`: Creates simple text responses.
    - `format_rich_response_with_chips`: Adds interactive chips for navigation.
    - `format_dialogflow_response_with_image_and_chips`: Combines images with text and chips.

2. **Session & Context Extraction**:
    - `extract_session`: Retrieves the session ID from the request body.
    - `extract_output_contexts`: Extracts context information from Dialogflow's response.

3. **Input Validation**:
    - `is_valid_email`: Validates the format of an email address.
    - `validate_name`: Ensures a name contains only alphabetic characters and spaces.

4. **Context Building**:
    - `build_contexts`: Generates output contexts to maintain session state.

5. **System Messages**:
    - `get_system_message`: Provides default system instructions for conversational AI design.

All functions are designed to be modular and reusable, with error handling and logging for debugging purposes.
"""




import re

import logging
def format_dialogflow_response(messages: list[str], output_contexts: list[dict] = None) -> dict:
    """
    Formats a response for Dialogflow's fulfillment API.

    Parameters:
        - messages (list[str]): A list of messages to be included in the response.
        - output_contexts (list[dict], optional): A list of contexts to include in the response. Default is None.

    Returns:
        - dict: A dictionary formatted for Dialogflow's fulfillment API, including:
            - 'fulfillmentMessages': A list of message objects for Dialogflow.
            - 'outputContexts' (optional): A list of contexts to maintain conversational state.

    Notes:
        - This function supports adding multiple messages to the response.
        - The `outputContexts` parameter is used to maintain session-specific data and flow control in Dialogflow.
    """


    logging.info("[format_dialogflow_response] Formatting response with messages: %s", messages)

    # Initialize output_contexts if None
    if output_contexts is None:
        output_contexts = []


    # Initialize the response with fulfillmentMessages
    response_data = {'fulfillmentMessages': []}


    # Add each message to the fulfillmentMessages
    for message in messages:
        response_data['fulfillmentMessages'].append(
            {
                'text': {
                    'text': [message]
                }
            }
        )

    # Include outputContexts if provided
    if output_contexts:
        response_data['outputContexts'] = output_contexts

    logging.debug("[format_dialogflow_response] Final response data: %s", response_data)

    return response_data





def format_rich_response_with_chips(messages: list[str], chips: list[str], output_contexts: list[dict] = None) -> dict:


    """
    Formats a rich response for Dialogflow's fulfillment API, including text messages and interactive chips.

    Parameters:
        - messages (list[str]): A list of plain text messages to include in the response.
        - chips (list[str]): A list of interactive chips (quick replies) for user selection.
        - output_contexts (list[dict], optional): A list of contexts to include in the response. Default is None.

    Returns:
        - dict: A dictionary formatted for Dialogflow's fulfillment API, including:
            - 'fulfillmentMessages': A list of plain text messages and rich content with chips.
            - 'outputContexts' (optional): A list of contexts to maintain conversational state.

    Notes:
        - Chips are useful for quick user responses, improving interactivity.
        - This function is ideal for rich responses combining text and user-friendly UI elements.
    """


    # Initialize output_contexts if None
    if output_contexts is None:
        output_contexts = []

    response_data = {'fulfillmentMessages': []}

    # Add plain text messages
    for message in messages:
        response_data['fulfillmentMessages'].append(
            {"text": {"text": [message]}}
        )

    # Add chips
    response_data['fulfillmentMessages'].append(
        {
            "payload": {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": [{"text": chip} for chip in chips]
                        }
                    ]
                ]
            }
        }
    )

    # Add output contexts if provided
    if output_contexts:
        response_data['outputContexts'] = output_contexts

    return response_data



#------------------------------------------------------------------------




def format_dialogflow_response_with_image_and_chips(messages: list[str], image_url: str, chips: list[str], output_contexts: list[dict] = None) -> dict:


    """
    Formats a Dialogflow response to include text messages, an image, and interactive chips (quick replies).

    Parameters:
        - messages (list[str]): A list of plain text messages to include in the response.
        - image_url (str): URL of the image to display.
        - chips (list[str]): A list of interactive chips (quick replies) for user selection.
        - output_contexts (list[dict], optional): A list of contexts to include in the response. Default is None.

    Returns:
        - dict: A dictionary formatted for Dialogflow's fulfillment API, including:
            - 'fulfillmentMessages': A list of text messages, an image, and rich content with chips.
            - 'outputContexts' (optional): A list of contexts to maintain conversational state.

    Notes:
        - Images can enhance the user experience by providing visual context.
        - Chips allow users to respond quickly, improving interactivity.
        - This function combines multiple elements for a rich response.
    """

    # Initialize output_contexts if None
    if output_contexts is None:
        output_contexts = []

    # Initialize response data
    response_data = {'fulfillmentMessages': []}

    # Add image to the response first
    if image_url:
        response_data['fulfillmentMessages'].append(
            {
                "payload": {
                    "richContent": [
                        [
                            {
                                "type": "image",
                                "rawUrl": image_url,
                                "accessibilityText": "Product Image"
                            }
                        ]
                    ]
                }
            }
        )

    # Add text messages to the response
    for message in messages:
        response_data['fulfillmentMessages'].append(
            {
                'text': {
                    'text': [message]
                }
            }
        )

    # Add chips to the response
    if chips:
        response_data['fulfillmentMessages'].append(
            {
                "payload": {
                    "richContent": [
                        [
                            {
                                "type": "chips",
                                "options": [{"text": chip} for chip in chips]
                            }
                        ]
                    ]
                }
            }
        )

    # Add output contexts if provided
    if output_contexts:
        response_data['outputContexts'] = output_contexts

    return response_data








def get_system_message():
    return {

            "role": "system",
            "content": (

                "You are a helpful assistant designed to provide information about Supercuts salons, their services, and locations. "
                "Your goal is to provide clear, concise, and accurately formatted answers based on the information provided to you.\n\n"

                "Supercuts has salons across various regions in the United States and Canada. Below is the directory of locations:\n\n"

                "**United States:**\n"
                "- Alabama\n"
                "- Arkansas\n"

                "**Canada:**\n"
                "- Nationwide\n\n"

                "Supercuts offers a wide range of services tailored to men, women, kids, and seniors. Below is an overview of the services provided:\n\n"

                "**Haircuts**\n"
                "- **Supercut®**: Includes a Haircut and Hot Towel Refresher, leaving you looking sharp and ready to go.\n"
                "- **Supercut Plus Shampoo**: Includes a Haircut, PLUS a Shampoo, and the Hot Towel Refresher.\n"
                "- Junior and senior discounts are available at most locations. Age limits may vary by location.\n\n"

                "**Color Services (Supercolor®)**\n"
                "- **Highlights**: Add visual interest with various highlighting techniques.\n"
                "- **Gray Blending**: Hide grays with a natural, blended look.\n"
                "- **Glazing**: Achieve richer, more dimensional color with semi-, demi-, or permanent color options.\n"
                "- **Tip Color**: Selectively color the ends of your hair for subtle or bold effects.\n\n"

                "**Additional Services**\n"
                "- **Tea Tree Experience**: A refreshing shampoo and conditioning service with an invigorating scalp massage and warm steamed towel for your face.\n"
                "- **Waxing**: Remove unwanted hair from brows, lips, or chin. (Available at select locations.)\n"
                "- **Styling**: Includes curling, flat iron, and blow-dry services. Prices vary based on hair length. (Available at select locations.)\n"
                "- **Beard Trims**: Keep your facial hair looking sharp with trims for beard, neckline, or mustache.\n\n"




				"**Products**\n"
				"- **Paul Mitchell Tea Tree Special Shampoo**\n"
				"  - **Description**: An invigorating cleanser that washes away impurities, leaving the scalp feeling fresh and clean. Formulated with tea tree oil, peppermint, and lavender, it provides a refreshing tingle and a pleasant aroma.\n"
				"  - **Key Benefits**:\n"
				"    - Deep cleanses the scalp and hair.\n"
				"    - Provides an invigorating sensation.\n"
				"    - Leaves hair full of vitality and luster.\n"
				"  - **Usage Instructions**: Apply a small amount to damp hair. Lather and massage into the scalp for a few minutes. Rinse thoroughly. Suitable for all hair types.\n"
				"  - **Availability**: Available at Supercuts salons and authorized retailers.\n\n"

				"- **Paul Mitchell Shampoo One**\n"
				"  - **Description**: A gentle shampoo designed to cleanse hair without stripping away essential moisture. Ideal for color-treated, fine, and medium hair types, it enhances manageability and adds deep shine.\n"
				"  - **Key Benefits**:\n"
				"    - Gently cleanses and improves manageability.\n"
				"    - Adds deep shine.\n"
				"    - Suitable for color-treated hair.\n"
				"  - **Usage Instructions**: Apply a small amount to wet hair. Lather and rinse completely. Gentle enough for daily use.\n"
				"  - **Availability**: Available at Supercuts salons and authorized retailers.\n\n"

				"- **MITCH by Paul Mitchell Double Hitter 2-in-1 Shampoo & Conditioner**\n"
				"  - **Description**: A sulfate-free formula that combines shampoo and conditioner in one step. It cleanses and conditions, leaving hair full and healthy-looking. Suitable for all hair types, especially fine to medium hair.\n"
				"  - **Key Benefits**:\n"
				"    - Cleanses and conditions in one step.\n"
				"    - Leaves hair with a healthy appearance.\n"
				"    - Sulfate-free formula.\n"
				"  - **Usage Instructions**: Lather into damp hair and rinse. Ideal for daily use.\n"
				"  - **Availability**: Available at Supercuts salons and authorized retailers.\n\n"



                "Adopt a professional yet friendly tone, similar to a customer service representative at Supercuts.\n\n"

                "When providing answers, always ensure proper formatting with clear spacing. Follow these formatting guidelines:\n"
                "- Use bullet points or numbered lists for details.\n"
                "- Place each bullet or numbered item on its own line with a blank line before and after the list.\n"
                "- Avoid compact formatting where multiple bullets are on the same line.\n"
                "- Add a blank line between sections to improve readability.\n\n"

                "Always lead the user to an action or follow-up, but ensure responses are concise and avoid repeating actions already mentioned. "
                "If you've provided guidance (e.g., 'provide your city or zip code'), avoid adding unnecessary additional follow-ups.\n\n"

                "Example:\n"
                "Question: 'What is Supercuts?'\n"
                "Answer:\n"
                "Supercuts is a hair salon franchise that offers professional haircuts and salon services. They are known for their convenient locations, affordable prices, and skilled stylists who provide quality haircuts to customers of all ages.\n\n"

                "Do you want to know more about our services or find a nearby location?\n\n"

                "When asked to explain a process (e.g., finding a location), break it into simple, numbered steps with clear spacing.\n"
                "Example:\n"
                "1. Visit the Supercuts website.\n\n"
                "2. Enter your ZIP code or city in the search bar.\n\n"
                "3. Browse the results to find a nearby salon.\n\n"

                "Provide examples when appropriate to clarify your answers. Ensure bullet points and numbered lists are properly formatted with each item appearing on its own line, and lists separated by blank lines.\n\n"
                "Keep responses concise and relevant. Provide additional details only when requested by the user."


				"When users ask for human assistance, contact information, or express dissatisfaction with the bot's responses, handle it professionally and redirect them appropriately:\n\n"
				"1. If users explicitly request to talk to someone (e.g., 'Can I talk to a person?'), provide the following response:\n"
				"- 'If you’d like to reach our team, you can contact us at support@example.com or call 123-456-7890.'\n\n"
				"2. If users request contact information (e.g., 'What’s your phone number?'), respond with:\n"
				"- 'You can contact us at support@example.com or call 123-456-7890.'\n\n"
				"3. If users mention incorrect details they’ve provided (e.g., 'I gave you the wrong email. Can I fix it?'), respond with:\n"
				"- 'If you need to update your details, please contact our team at support@example.com or call 123-456-7890.'\n\n"
				"Always keep these responses concise and professional, ensuring they address the user's concern directly and redirect them to appropriate resources."



            )
        }



#--------------------------------------------------------------------------------------------------------


def extract_session_parameters(output_contexts):

    """
    Extracts the session parameters from the 'session-parameters' context in the output contexts.

    Parameters:
        - output_contexts (list): A list of contexts from the Dialogflow webhook request.

    Returns:
        - dict: A dictionary of session parameters if the 'session-parameters' context is found.
                If not, an empty dictionary is returned.

    Raises:
        - TypeError: If the `output_contexts` parameter is not a list.


    Notes:
        - The function assumes that the context name for session parameters ends with '/contexts/session-parameters'.
        - If no such context exists, a warning is logged, and an empty dictionary is returned.
    """



    # Check if the input is a list; raise an error if not
    if not isinstance(output_contexts, list):
        raise TypeError("Output contexts must be a list.")


    # Iterate through the provided contexts to find 'session-parameters'
    for context in output_contexts:
        if context.get('name', '').endswith('/contexts/session-parameters'):
            return context.get('parameters', {})

    logging.warning("[extract_session_parameters] session-parameters context not found.")
    return {}




#------------------------------------------------------------------------------




def is_valid_email(email):
    """
    Validates an email address using a simplified regex pattern.

    Parameters:
        - email (str): The email address to validate.

    Returns:
        - bool: True if the email is valid (matches the pattern), False otherwise.

    Raises:
        - ValueError: If `email` is not a string.

    Notes:
        - The regex used is a simplified pattern that ensures the email contains:
            1. At least one character before the "@" symbol.
            2. At least one character after the "@" symbol.
            3. A period "." followed by at least one character (e.g., "example.com").
        - It is not an exhaustive validator for all edge cases (e.g., subdomains, special characters).
    """


    if not isinstance(email, str):
        raise ValueError("Email must be a string.")

    # Define a regex pattern to match a simplified email structure 
    pattern = r'^[^@]+@[^@]+\.[^@]+$'


    # Match the email against the pattern
    match = re.match(pattern, email)

    # Return True if the email matches the pattern, otherwise False
    return match is not None 







#--------------------------------------------------------------------------------------------------------



def validate_name(name: str) -> bool:

    """
    Validates a name to ensure it contains only alphabetic characters and spaces.

    Parameters:
        - name (str): The name to validate.

    Returns:
        - bool: True if the name is valid, False otherwise.

    Raises:
        - ValueError: If `name` is not a string.

    Notes:
        - Valid names must:
            1. Contain only uppercase or lowercase alphabetic characters.
            2. Allow spaces between words (e.g., "John Doe").
            3. Disallow special characters, numbers, or extra spaces.
    """



    if not isinstance(name, str):
        raise ValueError("Name must be a string.")


    # Match the name against the regex pattern
    # Pattern explanation:
    # ^[A-Za-z]+        - Start with one or more alphabetic characters.
    # (?: [A-Za-z]+)*   - Allow zero or more groups of a space followed by alphabetic characters.
    # $                 - End of string.

    return re.match(r'^[A-Za-z]+(?: [A-Za-z]+)*$', name) is not None






#--------------------------------------------------------------------------------------------------------


##USER BUILDS OUTPUT CONTEXT


def build_contexts(session: str, next_context: str, session_parameters: dict, lifespan: int = 99) -> list:
    """
    Builds output contexts for Dialogflow, specifying the next context and session parameters.

    Parameters:
        - session (str): Dialogflow session ID (unique to each user interaction).
        - next_context (str): The name of the next context (e.g., "await-name").
        - session_parameters (dict): A dictionary of session parameters to include.
        - lifespan (int): Lifespan of the session-parameters context (default is 99).

    Returns:
        - list: A list of context dictionaries formatted for Dialogflow.


    Notes:
        - The `next_context` context is used to determine the next step in the conversation flow.
        - The `session-parameters` context persists session data for future intents.
    """



    logging.info("[build_contexts] Building contexts for session: %s, next_context: %s", session, next_context)


    # Construct the list of contexts
    contexts = [
        # Context for the next action with a short lifespan
        {
            'name': f'{session}/contexts/{next_context}',
            'lifespanCount': 1
        },
        {

        # Session parameters context with a customizable lifespan
            'name': f'{session}/contexts/session-parameters',
            'lifespanCount': lifespan,
            'parameters': session_parameters
        }
    ]
    logging.debug("[build_contexts] Built contexts: %s", contexts)
    return contexts



#--------------------------------------------------------------------------------------------------


def extract_session(body: dict) -> str:
    """
    Extracts the session ID from the Dialogflow webhook request payload.
    Validates the presence and format of the session ID.

    Parameters:
        - body (dict): Dialogflow webhook request payload containing the 'session' key.

    Returns:
        - str: The extracted session ID if it exists and is valid.

    Raises:
        - ValueError: If the request body is missing, malformed, or the session format is invalid.

    Notes:
        - The session ID should follow the format: "projects/<project-id>/agent/sessions/<session-id>".
        - This utility function ensures the request is properly formatted before proceeding with any Dialogflow interaction.
    """


    try:
        # Check if the request body is None
        if body is None:
            logging.warning("[extract_session] Missing request body.")
            raise ValueError("Missing request body.")

        # Check if the 'session' key exists in the body
        if 'session' not in body:
            logging.warning("[extract_session] Missing 'session' in request body.")
            raise ValueError("Missing 'session' in request body.")

        session = body['session']

        # Validate that the session is a string
        if not isinstance(session, str):
            logging.warning("[extract_session] 'session' is not a string.")
            raise ValueError("'session' must be a string.")

        # Validate the session format (e.g., "projects/.../sessions/...")
        if not session.startswith("projects/") or "/sessions/" not in session:
            logging.warning(f"[extract_session] Invalid session format: {session}")
            raise ValueError("Invalid 'session' format. Must follow 'projects/.../sessions/...'.")
        
        return session

    except ValueError as e:
        logging.error(f"[extract_session] Error extracting session: {e}")
        raise

#--------------------------------------------------------------------------------------------------


def extract_output_contexts(body: dict) -> list:
    """
    Extracts the `outputContexts` from the Dialogflow webhook request payload.
    Ensures that the `outputContexts` field exists and is properly formatted as a list.

    Parameters:
        - body (dict): Dialogflow webhook request payload containing the 'queryResult' key.

    Returns:
        - list: A list of output contexts extracted from the payload.

    Raises:
        - ValueError: If `outputContexts` is not a list.
        - Exception: If the request body or 'queryResult' key is malformed or missing.

    Notes:
        - `outputContexts` is an optional part of the Dialogflow webhook payload, but if present,
          it must be a list. This function validates its structure.
    """


    try:
        output_contexts = body['queryResult'].get('outputContexts', [])
        if not isinstance(output_contexts, list):
            logging.warning("[extract_output_contexts] 'outputContexts' is not a list.")
            raise ValueError("'outputContexts' should be a list.")
        return output_contexts
    except Exception as e:
        logging.error(f"[extract_output_contexts] Error extracting output contexts: {e}")
        raise


from utils.config import WORKING_HOURS


import pytz
from datetime import datetime, timedelta

def is_within_working_hours(date_time: str, timezone: str ="Europe/Belgrade" ) -> bool:
    try:
        # Parse and adjust to the user's timezone
        dt = datetime.fromisoformat(date_time)
        if dt.tzinfo is None:
            dt = pytz.timezone(timezone).localize(dt)
        local_time = dt.astimezone(pytz.timezone(timezone))

        # Log the parsed and adjusted times
        logging.info(f"Input time: {date_time}, Local time: {local_time}, Hour: {local_time.hour}")

        # Check working hours
        hour = local_time.hour
        return WORKING_HOURS["start"] <= hour < WORKING_HOURS["end"]

    except Exception as e:
        logging.error(f"[is_within_working_hours] Error: {e}", exc_info=True)
        return False











