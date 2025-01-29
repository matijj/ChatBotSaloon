import pytest
from unittest.mock import patch
from utils.action_handlers import default_welcome_intent

# Test cases for  DEFAULT_WELCOME_INTENT
def test_default_welcome_intent_valid():
    # Mock a valid body
    body = {
        "session": "projects/test_project/agent/sessions/test_session"
    }

    # Expected response structure
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Hi there! I’m here to assist you. Here’s what I can do for you:"]}},
            {"text": {"text": ["-Provide our business hours and location."]}},
            {"text": {"text": ["-Tell you about our services."]}},
            {"text": {"text": ["-Help you claim a 10% discount!"]}},
            {"text": {"text": ["Just say 'Claim Discount' to get started."]}}
        ]
    }

    # Call the function
    response = default_welcome_intent(body)

    # Validate the response
    assert response == expected_response

def test_default_welcome_intent_missing_session():
    # Mock a body without 'session'
    body = {}

    # Call the function and expect a KeyError
    with pytest.raises(KeyError):
        default_welcome_intent(body)

def test_default_welcome_intent_unexpected_body():
    # Mock a malformed body
    body = {"unexpectedKey": "unexpectedValue"}

    # Call the function and expect a KeyError
    with pytest.raises(KeyError):
        default_welcome_intent(body)

def test_default_welcome_intent_helper_function_call():
    # Mock a valid body
    body = {
        "session": "projects/test_project/agent/sessions/test_session"
    }

    # Mock the helper function
    with patch("utils.action_handlers.format_dialogflow_response") as mock_helper:
        # Define what the mock should return
        mock_helper.return_value = {"mock": "response"}

        #print("Mock setup:", mock_helper)

        # Call the function
        response = default_welcome_intent(body)

        # Debugging: Print the response from the function
        #print("Response from default_welcome_intent:", response)

        # Debugging: Ensure the mock is set up correctly
        #print("Mock call args during test:", mock_helper.call_args_list)

        # Ensure the helper function was called with the correct arguments
        mock_helper.assert_called_once_with([
            "Hi there! I’m here to assist you. Here’s what I can do for you:",
            "-Provide our business hours and location.",
            "-Tell you about our services.",
            "-Help you claim a 10% discount!",
            "Just say 'Claim Discount' to get started."
        ], [])



#----------------------------------------------------------------------------------------------------------------------------------



import pytest
from utils.action_handlers import handle_wants_to_claim_discount

def test_handle_wants_to_claim_discount_valid():
    # Step 1: Mock a valid payload
    body = {
        "session": "projects/test_project/agent/sessions/test_session"
    }

    # Step 2: Define expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Great! To activate your 10% discount, let’s start with your name. What’s your name?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "person": "",
                    "email": ""
                }
            }
        ]
    }

    # Step 3: Call the function
    response = handle_wants_to_claim_discount(body)

    # Step 4: Validate the response
    assert response == expected_response



def test_handle_wants_to_claim_discount_missing_session():
    # Mock a body without the 'session' key
    body = {}

    # Expect a KeyError when the 'session' key is missing
    with pytest.raises(KeyError):
        handle_wants_to_claim_discount(body)





def test_handle_wants_to_claim_discount_helper_function_call():
    body = {
        "session": "projects/test_project/agent/sessions/test_session"
    }

    # Mock the helper function as it's imported into action_handlers
    with patch("utils.action_handlers.format_dialogflow_response") as mock_helper:
        # Define what the mock should return
        mock_helper.return_value = {"mock": "response"}

        # Call the function
        response = handle_wants_to_claim_discount(body)

        # Ensure the helper function was called with the correct arguments
        mock_helper.assert_called_once_with(
            ["Great! To activate your 10% discount, let’s start with your name. What’s your name?"],
            [
                {'name': 'projects/test_project/agent/sessions/test_session/contexts/await-name', 'lifespanCount': 1},
                {
                    'name': 'projects/test_project/agent/sessions/test_session/contexts/session-parameters',
                    'lifespanCount': 99,
                    'parameters': {"person": "", "email": ""}
                }
            ]
        )

        # Validate the mocked response
        assert response == {"mock": "response"}





#-----------------------------------
#HANDLE_USER_PROVIDES_NAME

import pytest
from unittest.mock import patch
from utils.action_handlers import handle_user_provides_name


def test_handle_user_provides_name_valid():
    # Step 1: Mock a valid payload
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "parameters": {
                "person.original": "John Doe"
            },
            "outputContexts": []
        }
    }

    # Step 2: Define the expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Thanks for your name, John Doe! What’s your email?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "person": "John Doe"
                }
            }
        ]
    }

    # Step 3: Call the function
    response = handle_user_provides_name(body)

    # Step 4: Validate the response
    assert response == expected_response




def test_handle_user_provides_name_empty_name():
    # Mock a payload with an empty name
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "parameters": {
                "person": {"original": ""}
            }
        }
    }

    # Define expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid name. Please avoid special characters or numbers."]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99
            }
        ]
    }

    # Call the function and validate response
    response = handle_user_provides_name(body)
    assert response == expected_response

def test_handle_user_provides_name_invalid_name():
    # Mock a payload with an invalid name
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "parameters": {
                "person": {"original": "John123"}
            }
        }
    }

    # Define expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid name. Please avoid special characters or numbers."]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99
            }
        ]
    }

    # Call the function and validate response
    response = handle_user_provides_name(body)
    assert response == expected_response





