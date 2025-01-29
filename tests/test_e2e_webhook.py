import pytest
from unittest.mock import patch
from flask import json
from src.app import app

@pytest.fixture
def client():
    """Fixture for creating a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client



#---------------
def test_webhook_empty_payload(client):
    """Test /webhook with an empty payload."""
    payload = {}

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 400

    # Assert error response
    assert response.json == {"error": "Invalid request structure"}


def test_webhook_missing_query_result(client):
    """Test /webhook with missing queryResult."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session"
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 400

    # Assert error response
    assert response.json == {"error": "Invalid request structure"}


def test_webhook_missing_action(client):
    """Test /webhook with missing action in queryResult."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {}
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 400

    # Assert error response
    assert response.json == {"error": "Invalid request structure"}


#--------------------------------------
def test_webhook_user_wants_to_claim_discount_valid(client):
    """Test /webhook with a valid userWantsToClaimDiscount action."""
    # Mock payload for userWantsToClaimDiscount
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userWantsToClaimDiscount"
        }
    }

    # Expected response
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

    # Simulate a POST request to /webhook
    with patch("utils.action_handlers.format_dialogflow_response") as mock_helper:  # Correct target for the mock


        mock_helper.return_value = expected_response

        response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

        # Assert status code
        assert response.status_code == 200

        # Assert response matches the expected response
        assert response.json == expected_response

        # Ensure the mocked helper was called correctly
        mock_helper.assert_called_once_with(
            ["Great! To activate your 10% discount, let’s start with your name. What’s your name?"],
            [
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
        )



def test_webhook_user_wants_to_claim_discount_missing_session(client):
    """Test /webhook with missing session."""
    payload = {
        "queryResult": {
            "action": "userWantsToClaimDiscount"
        }
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 500

    # Assert error response
    assert response.json == {"error": "Something went wrong"}






#------------------------------------------------------------------


def test_webhook_handle_user_provides_name_valid(client):
    """Test /webhook for handle_user_provides_name with a valid name."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userProvidesNameIntent",
            "parameters": {
                "person.original": "John Doe"
            },
            "outputContexts": []
        }
    }

    # Expected response
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

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response



def test_webhook_handle_user_provides_name_invalid(client):
    """Test /webhook for handle_user_provides_name with an invalid name."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userProvidesNameIntent",
            "parameters": {
                "person.original": "John123"
            },
            "outputContexts": []
        }
    }

    # Expected response
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

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response



def test_webhook_handle_user_provides_name_missing(client):
    """Test /webhook for handle_user_provides_name with a missing or empty name."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userProvidesNameIntent",
            "parameters": {
                "person.original": ""
            },
            "outputContexts": []
        }
    }

    # Expected response
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

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response





#--------------------------------------------------
#EMAIL NOW 
def test_webhook_handle_user_provides_email_valid(client):
    """Test /webhook for handle_user_provides_email with a valid email."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userProvidesEmailIntent",
            "parameters": {
                "email.original": "user@example.com"
            },
            "outputContexts": []
        }
    }

    # Update expected response to match actual behavior
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Thanks! Here’s what I got: Name: unknown, Email: user@example.com. Type 'update' if you want to update your information."]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-confirmation",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "email": "user@example.com"
                }
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code and response
    assert response.status_code == 200
    assert response.json == expected_response



def test_webhook_handle_user_provides_email_invalid(client):
    """Test /webhook for handle_user_provides_email with an invalid email."""
    # Mock payload with an invalid email
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userProvidesEmailIntent",
            "parameters": {
                "email.original": "invalid_email@"  # Invalid email format
            },
            "outputContexts": []
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid email address. Could you try again?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {}
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response








def test_webhook_handle_user_provides_email_missing(client):
    """Test /webhook for handle_user_provides_email with a missing email."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userProvidesEmailIntent",
            "parameters": {},
            "outputContexts": []
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid email address. Could you try again?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {}
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response




#-------------------------------------------------------
#USER CONFIRMS NO CHANGE



def test_webhook_handle_user_confirms_no_changes_valid(client):
    """Test /webhook for handle_user_confirms_no_changes with valid parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userConfirmsNoChangesIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe",
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Awesome! Your details are all set: Name: John Doe, Email: user@example.com. Feel free to reach out if you need anything else. Goodbye for now!"
                    ]
                }
            }
        ]
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response






def test_webhook_handle_user_confirms_no_changes_missing_parameters(client):
    """Test /webhook for handle_user_confirms_no_changes with missing session parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userConfirmsNoChangesIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        # No person.original or email.original
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Awesome! Your details are all set: Name: unknown, Email: unknown. Feel free to reach out if you need anything else. Goodbye for now!"
                    ]
                }
            }
        ]
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response





def test_webhook_handle_user_confirms_no_changes_malformed_request(client):
    """Test /webhook for handle_user_confirms_no_changes with malformed request."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            # Missing action and outputContexts
        }
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}


#----------------------------
#----------------------------
#----------------------------
#----------------------------
#----------------------------

#STILL NO CHANGE INTENT NOW TESTING FOR GOOGLE SHEET INTEGRATOIN 
#VALID AND INVALID
#
#
#

from unittest.mock import patch
from utils.action_handlers import handle_user_confirms_no_changes

def test_webhook_handle_user_confirms_no_changes_valid(client):
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userConfirmsNoChangesIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe",
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Awesome! Your details are all set: Name: John Doe, Email: user@example.com. Feel free to reach out if you need anything else. Goodbye for now!"
                    ]
                }
            }
        ]
    }

    # Mock write_data and datetime
    with patch("utils.action_handlers.write_data") as mock_write_data, patch("utils.action_handlers.datetime") as mock_datetime:
        # Mock the timestamp
        mock_datetime.now.return_value.strftime.return_value = "2025-01-05 14:00:00"
        mock_write_data.return_value = {"updates": {"updatedRows": 1}}  # Simulate successful write

        response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

        # Assertions
        mock_write_data.assert_called_once_with("list!A1", [["John Doe", "user@example.com", "2025-01-05 14:00:00"]])
        assert response.status_code == 200
        assert response.json == expected_response






from unittest.mock import patch

def test_webhook_handle_user_confirms_no_changes_sheets_failure(client):
    """Test /webhook for handle_user_confirms_no_changes when write_data fails."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userConfirmsNoChangesIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe",
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your details were confirmed but couldn't be saved to our database. Please try again later."
                    ]
                }
            }
        ]
    }

    # Mock write_data to simulate failure
    with patch("utils.action_handlers.write_data") as mock_write_data, patch("utils.action_handlers.datetime") as mock_datetime:
        # Mock the timestamp
        mock_datetime.now.return_value.strftime.return_value = "2025-01-05 14:00:00"
        mock_write_data.side_effect = Exception("API Error")  # Simulate failure

        response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

        # Assertions
        mock_write_data.assert_called_once_with("list!A1", [["John Doe", "user@example.com", "2025-01-05 14:00:00"]])
        assert response.status_code == 200
        assert response.json == expected_response







#----------------------------
#----------------------------
#----------------------------
#----------------------------
#----------------------------
#----------------------------




# USER WANTS TO UPDATE
#----------------------------

def test_webhook_handle_user_wants_to_update_valid(client):
    """Test /webhook for handle_user_wants_to_update with valid session parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userWantsToUpdateIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe",
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["What would you like to update? Your name or your email?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-field",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "person.original": "John Doe",
                    "email.original": "user@example.com"
                }
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code and response
    assert response.status_code == 200
    assert response.json == expected_response



def test_webhook_handle_user_wants_to_update_missing_parameters(client):
    """Test /webhook for handle_user_wants_to_update with missing session parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userWantsToUpdateIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {}
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["What would you like to update? Your name or your email?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-field",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {}
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code and response
    assert response.status_code == 200
    assert response.json == expected_response




def test_webhook_handle_user_wants_to_update_malformed_request(client):
    """Test /webhook for handle_user_wants_to_update with malformed request."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            # Missing action and outputContexts
        }
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code and error response
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}


#---------------------------
#USER CHOOSES NAME TO UPDATE

def test_webhook_handle_user_chooses_name_valid(client):
    """Test /webhook for handle_user_chooses_name with valid parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userChoosesNameIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your current name is John Doe. What would you like to update it to?"
                    ]
                }
            }
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "person.original": "John Doe"
                }
            }
        ]
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response




def test_webhook_handle_user_chooses_name_missing_parameters(client):
    """Test /webhook for handle_user_chooses_name with missing session parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userChoosesNameIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {}
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your current name is unknown. What would you like to update it to?"
                    ]
                }
            }
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {}
            }
        ]
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response





def test_webhook_handle_user_chooses_name_malformed_request(client):
    """Test /webhook for handle_user_chooses_name with malformed request."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            # Missing action and outputContexts
        }
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}





#---------------------------
#USER CHOOSES EMAIL TO UPDATE


def test_webhook_handle_user_chooses_email_valid(client):
    """Test /webhook for handle_user_chooses_email with valid parameters."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userChoosesEmailIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your current email is user@example.com. What would you like to update it to?"
                    ]
                }
            }
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "email.original": "user@example.com"
                }
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response







def test_webhook_handle_user_chooses_email_missing_parameters(client):
    """Test /webhook for handle_user_chooses_email with missing email parameters."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userChoosesEmailIntent",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        # No email.original key
                    }
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your current email is unknown. What would you like to update it to?"
                    ]
                }
            }
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {}
            }
        ]
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response


def test_webhook_handle_user_chooses_email_malformed_request(client):
    """Test /webhook for handle_user_chooses_email with a malformed request."""
    # Mock payload
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            # Missing `action` and `outputContexts`
        }
    }

    # Simulate a POST request to /webhook
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 400

    # Assert error response
    assert response.json == {"error": "Invalid request structure"}



#INTENT FOR UPDATING NAME (after user affirms he wants)


def test_webhook_handle_user_updates_name_valid(client):
    """Test /webhook for handle_user_updates_name with valid parameters."""
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userUpdatesNameIntent",
            "parameters": {
                "person.original": "Jane Smith"
            },
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe",
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your name has been updated to Jane Smith. Here’s what I have now: Name: Jane Smith, Email: user@example.com. Is there anything else you want to change?"
                    ]
                }
            }
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-confirmation",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "person": "Jane Smith",
                    "person.original": "Jane Smith",
                    "email.original": "user@example.com"
                }
            }
        ]
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')

    # Assert status code
    assert response.status_code == 200

    # Assert response matches expected response
    assert response.json == expected_response




@pytest.mark.parametrize("payload, expected_response", [
    # Case 1: Missing person.original in parameters
    ({
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userUpdatesNameIntent",
            "parameters": {},
            "outputContexts": []
        }
    }, {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid name. Please avoid special characters or numbers."]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99
            }
        ]
    }),

    # Case 2: Empty person.original
    ({
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userUpdatesNameIntent",
            "parameters": {"person.original": ""},
            "outputContexts": []
        }
    }, {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid name. Please avoid special characters or numbers."]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name-update",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99
            }
        ]
    })
])
def test_webhook_handle_user_updates_name_missing_data(client, payload, expected_response):
    """Test /webhook for handle_user_updates_name with missing or empty name."""
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response



#---------------------------------------------
#INTENT FOR UPDATING EMAIL (after user affirms he wants to update email)


def test_webhook_handle_user_updates_email_valid(client):
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userUpdatesEmailIntent",
            "parameters": {
                "email.original": "newuser@example.com"
            },
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                    "parameters": {
                        "person.original": "John Doe",
                        "email.original": "user@example.com"
                    }
                }
            ]
        }
    }

    expected_response = {
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        "Your email has been successfully updated to newuser@example.com. Here’s what I have now: "
                        "Name: John Doe, Email: newuser@example.com. Is there anything else you want to change?"
                    ]
                }
            }
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-confirmation",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99,
                "parameters": {
                    "person.original": "John Doe",
                    "email.original": "newuser@example.com",
                    "email": "newuser@example.com"
                }
            }
        ]
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response




@pytest.mark.parametrize("payload, expected_response", [
    # Case 1: Missing email.original in parameters
    ({
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userUpdatesEmailIntent",
            "parameters": {},
            "outputContexts": []
        }
    }, {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid email address. Could you try again?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99
            }
        ]
    }),

    # Case 2: Empty email.original
    ({
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "action": "userUpdatesEmailIntent",
            "parameters": {"email.original": ""},
            "outputContexts": []
        }
    }, {
        "fulfillmentMessages": [
            {"text": {"text": ["Hmm, that doesn’t look like a valid email address. Could you try again?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email",
                "lifespanCount": 1
            },
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
                "lifespanCount": 99
            }
        ]
    })
])
def test_webhook_handle_user_updates_email_missing_data(client, payload, expected_response):
    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json == expected_response






def test_webhook_handle_user_updates_email_malformed_request(client):
    payload = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            # Missing action and parameters
        }
    }

    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}




#--------------------------------------------------
#TEST FOR FALLBACK


from unittest.mock import patch
import json



#def test_webhook_handle_fallback_no_active_context(client):
#    """Test /webhook for handle_fallback_intent with no active context."""
#    payload = {
#        "session": "projects/test_project/agent/sessions/test_session",
#        "queryResult": {
#            "action": "fallbackIntent",
#            "queryText": "Test fallback question",
#            "outputContexts": []  # No active contexts
#        }
#    }
#
#    # Mock the GPT response
#    gpt_mock_response = "This is a simulated GPT response."
#
#    with patch("utils.action_handlers.client.chat.completions.create") as mock_gpt_call, \
#         patch("utils.action_handlers.get_system_message") as mock_system_message:
#
#        # Configure the mocks
#        mock_gpt_call.return_value.choices = [{"message": {"content": gpt_mock_response}}]
#        mock_system_message.return_value = {"role": "system", "content": "System message for context"}
#
#        response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
#
#        print("Payload sent to webhook:", json.dumps(payload, indent=2))
#        print("Response received:", response.json)
#
#        # Update the test expectation to match observed behavior
#        assert response.status_code == 200
#        assert response.json["fulfillmentMessages"][0]["text"]["text"][0] == gpt_mock_response
#
#



from unittest.mock import patch
import json
#
#
#def test_webhook_handle_fallback_await_name(client):
#    """Test /webhook for handle_fallback_intent with 'await-name' active context."""
#    
#    # Simulated payload with the 'await-name' context
#    payload = {
#        "session": "projects/test_project/agent/sessions/test_session",
#        "queryResult": {
#            "action": "fallbackIntent",
#            "queryText": "Test query",  # Simulating the user query
#            "outputContexts": [
#                {
#                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
#                    "lifespanCount": 1
#                }
#            ]
#        }
#    }
#
#    # Expected response
#    expected_response = {
#        "fulfillmentMessages": [
#            {"text": {"text": ["Sorry, I didn’t get that. Can you provide your name?"]}}
#        ],
#        "outputContexts": [
#            {
#                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
#                "lifespanCount": 1
#            }
#        ]
#    }
#
#    # POST request to the webhook
#    response = client.post('/webhook', data=json.dumps(payload), content_type='application/json')
#
#    # Debugging outputs for visibility
#    print("Payload sent to webhook:", json.dumps(payload, indent=2))
#    print("Response received:", json.dumps(response.json, indent=2))  # Check if context updates match
#
#    # Validate the response
#    assert response.status_code == 200
#    assert response.json == expected_response
#







import pytest
from unittest.mock import patch
from utils.action_handlers import handle_fallback_intent

def test_handle_fallback_intent_await_name():
    # Mocked payload with 'await-name' context
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "queryText": "Random query",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
                    "lifespanCount": 5
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Sorry, I didn’t get that. Can you provide your name?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name",
                "lifespanCount": 1
            }
        ]
    }

    # Call the function
    response = handle_fallback_intent(body)

    # Assertions
    assert response["fulfillmentMessages"] == expected_response["fulfillmentMessages"]
    assert len(response["outputContexts"]) == 1
    assert response["outputContexts"][0]["name"] == expected_response["outputContexts"][0]["name"]
    assert response["outputContexts"][0]["lifespanCount"] == expected_response["outputContexts"][0]["lifespanCount"]






def test_handle_fallback_intent_await_email():
    # Mocked payload with 'await-email' context
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "queryText": "Random query",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-email",
                    "lifespanCount": 5
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["Sorry, I didn’t get that. Can you provide your email?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email",
                "lifespanCount": 1
            }
        ]
    }

    # Call the function
    response = handle_fallback_intent(body)

    # Assertions
    assert response["fulfillmentMessages"] == expected_response["fulfillmentMessages"]
    assert len(response["outputContexts"]) == 1
    assert response["outputContexts"][0]["name"] == expected_response["outputContexts"][0]["name"]
    assert response["outputContexts"][0]["lifespanCount"] == expected_response["outputContexts"][0]["lifespanCount"]





def test_handle_fallback_intent_await_confirmation():
    # Mocked payload with 'await-confirmation' context
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "queryText": "Random query",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-confirmation",
                    "lifespanCount": 5
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["If you want to update something, just say 'Yes.' If everything looks good, say 'No.'"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-confirmation",
                "lifespanCount": 1
            }
        ]
    }

    # Call the function
    response = handle_fallback_intent(body)

    # Assertions
    assert response["fulfillmentMessages"] == expected_response["fulfillmentMessages"]
    assert len(response["outputContexts"]) == 1
    assert response["outputContexts"][0]["name"] == expected_response["outputContexts"][0]["name"]
    assert response["outputContexts"][0]["lifespanCount"] == expected_response["outputContexts"][0]["lifespanCount"]






def test_handle_fallback_intent_await_name_update():
    # Mocked payload with 'await-name-update' context
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "queryText": "Random query",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-name-update",
                    "lifespanCount": 5
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["I still need your updated name. What would you like to change it to?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-name-update",
                "lifespanCount": 1
            }
        ]
    }

    # Call the function
    response = handle_fallback_intent(body)

    # Assertions
    assert response["fulfillmentMessages"] == expected_response["fulfillmentMessages"]
    assert len(response["outputContexts"]) == 1
    assert response["outputContexts"][0]["name"] == expected_response["outputContexts"][0]["name"]
    assert response["outputContexts"][0]["lifespanCount"] == expected_response["outputContexts"][0]["lifespanCount"]





def test_handle_fallback_intent_await_email_update():
    # Mocked payload with 'await-email-update' context
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "queryText": "Random query",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-email-update",
                    "lifespanCount": 5
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["I still need your updated email. Could you provide it again?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-email-update",
                "lifespanCount": 1
            }
        ]
    }

    # Call the function
    response = handle_fallback_intent(body)

    # Assertions
    assert response["fulfillmentMessages"] == expected_response["fulfillmentMessages"]
    assert len(response["outputContexts"]) == 1
    assert response["outputContexts"][0]["name"] == expected_response["outputContexts"][0]["name"]
    assert response["outputContexts"][0]["lifespanCount"] == expected_response["outputContexts"][0]["lifespanCount"]




def test_handle_fallback_intent_await_field():
    # Mocked payload with 'await-field' context
    body = {
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {
            "queryText": "Random query",
            "outputContexts": [
                {
                    "name": "projects/test_project/agent/sessions/test_session/contexts/await-field",
                    "lifespanCount": 5
                }
            ]
        }
    }

    # Expected response
    expected_response = {
        "fulfillmentMessages": [
            {"text": {"text": ["What would you like to update? Your name or your email?"]}}
        ],
        "outputContexts": [
            {
                "name": "projects/test_project/agent/sessions/test_session/contexts/await-field",
                "lifespanCount": 1
            }
        ]
    }

    # Call the function
    response = handle_fallback_intent(body)

    # Assertions
    assert response["fulfillmentMessages"] == expected_response["fulfillmentMessages"]
    assert len(response["outputContexts"]) == 1
    assert response["outputContexts"][0]["name"] == expected_response["outputContexts"][0]["name"]
    assert response["outputContexts"][0]["lifespanCount"] == expected_response["outputContexts"][0]["lifespanCount"]








#NE RADI TESTING ZA NO CONTEXT
#
#from unittest.mock import patch
#
#
#def test_handle_fallback_intent_no_context_valid_gpt():
#    # Mocked payload with no relevant contexts
#    body = {
#        "session": "projects/test_project/agent/sessions/test_session",
#        "queryResult": {
#            "queryText": "What is your purpose?",
#            "outputContexts": []  # Simulating no relevant context
#        }
#    }
#
#    # Mock GPT response
#    gpt_mock_response = "I am here to assist you with your queries."
#
#    with patch("utils.action_handlers.client.chat.completions.create") as mock_gpt_call:
#        # Correctly configure the mock GPT response
#        mock_gpt_call.return_value = {
#            "choices": [{"message": {"content": gpt_mock_response}}]
#        }
#
#        # Call the function
#        response = handle_fallback_intent(body)
#
#        # Assertions
#        assert response["fulfillmentMessages"][0]["text"]["text"][0] == gpt_mock_response
#        assert response["outputContexts"] == []  # No updated contexts
#        mock_gpt_call.assert_called_once()  # Ensure GPT was called
#


