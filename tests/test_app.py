import pytest
from src.app import app

# Define the client fixture
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test case for the home endpoint
def test_handle_home(client):
    # Simulate a GET request to the home endpoint
    response = client.get('/')
    
    # Assert the status code is 200
    assert response.status_code == 200
    
    # Assert the response body is "OK"
    assert response.get_data(as_text=True) == "OK"



#------------------------------------------------------------


def test_webhook_empty_body(client):
    # Test an empty body
    response = client.post('/webhook', json={})
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}

def test_webhook_missing_query_result(client):
    # Test missing 'queryResult' key
    response = client.post('/webhook', json={"someOtherKey": {}})
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}

def test_webhook_missing_action(client):
    # Test missing 'action' within 'queryResult'
    response = client.post('/webhook', json={"queryResult": {}})
    assert response.status_code == 400
    assert response.json == {"error": "Invalid request structure"}


#------------------------------------------------------------


from flask import Flask
from flask.testing import FlaskClient
import pytest
from unittest.mock import patch
from src.app import app


from unittest.mock import patch

def test_webhook_valid_action(client):
    # Mock a handler
    with patch('src.app.action_handlers') as mock_handlers:
        mock_handlers.get.return_value = lambda x: {"fulfillmentMessages": [{"text": {"text": ["Mock response!"]}}]}
        
        response = client.post('/webhook', json={
            "session": "projects/test_project/agent/sessions/test_session",
            "queryResult": {"action": "validAction"}
        })

        assert response.status_code == 200
        assert response.json == {"fulfillmentMessages": [{"text": {"text": ["Mock response!"]}}]}
        mock_handlers.get.assert_called_with("validAction")



def test_webhook_unknown_action(client):
    response = client.post('/webhook', json={
        "session": "projects/test_project/agent/sessions/test_session",
        "queryResult": {"action": "unknownAction"}
    })
    assert response.status_code == 200
    assert response.json == {"fulfillmentMessages": [{"text": {"text": ["Sorry, I didn’t understand."]}}]}



def test_webhook_internal_error(client):
    with patch('src.app.action_handlers') as mock_handlers:
        mock_handlers.get.side_effect = Exception("Test exception")
        response = client.post('/webhook', json={
            "session": "projects/test_project/agent/sessions/test_session",
            "queryResult": {"action": "validAction"}
        })
        assert response.status_code == 500
        assert response.json == {"error": "Something went wrong"}


#--------------------------------------------















