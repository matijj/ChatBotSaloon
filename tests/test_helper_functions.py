import pytest

#------------------------------------------------------------------
from utils.helper_functions import validate_name


# validate_name
def test_validate_name_valid():
    # Valid names
    assert validate_name("John Doe") == True
    assert validate_name("Alice") == True
    assert validate_name("Mary Jane Watson") == True

def test_validate_name_invalid():
    # Invalid names
    assert validate_name("123John") == False
    assert validate_name("John@123") == False
    assert validate_name("") == False
    assert validate_name(" ") == False
    assert validate_name("John  Doe") == False  # Multiple spaces
    assert validate_name("O'Connor") == False  # Special characters

def test_validate_name_non_string_input():
    # Non-string inputs
    with pytest.raises(ValueError):
        validate_name(123)
    with pytest.raises(ValueError):
        validate_name(None)


#------------------------------------------------------------------

from utils.helper_functions import is_valid_email


def test_is_valid_email_valid():
    # Valid emails
    assert is_valid_email("test@example.com") == True
    assert is_valid_email("john.doe@domain.co") == True
    assert is_valid_email("user123@company.org") == True

def test_is_valid_email_invalid():
    # Invalid emails
    assert is_valid_email("invalid-email") == False
    assert is_valid_email("missing@domain") == False
    assert is_valid_email("@example.com") == False
    assert is_valid_email("test@.com") == False
    assert is_valid_email("") == False

def test_is_valid_email_non_string_input():
    # Non-string inputs
    with pytest.raises(ValueError):
        is_valid_email(123)
    with pytest.raises(ValueError):
        is_valid_email(None)


#------------------------------------------------------------------

from utils.helper_functions import build_contexts

# Test cases for build_contexts

def test_build_contexts_valid():
    session = "test_session"
    next_context = "await-email"
    session_parameters = {"person": "John", "email": "john@example.com"}
    lifespan = 99

    result = build_contexts(session, next_context, session_parameters, lifespan)
    assert len(result) == 2
    assert result[0] == {
        'name': "test_session/contexts/await-email",
        'lifespanCount': 1
    }
    assert result[1] == {
        'name': "test_session/contexts/session-parameters",
        'lifespanCount': 99,
        'parameters': session_parameters
    }

def test_build_contexts_empty_session_parameters():
    session = "test_session"
    next_context = "await-email"
    session_parameters = {}
    lifespan = 50

    result = build_contexts(session, next_context, session_parameters, lifespan)
    assert result[1]["parameters"] == {}



#---------------------------------------------------------------
from utils.helper_functions import format_dialogflow_response

# Test cases for format_dialogflow_response

def test_format_dialogflow_response_valid():
    # Valid inputs with output contexts
    messages = ["Hello!", "How can I help you?"]
    output_contexts = [{"name": "test_context", "lifespanCount": 1}]
    response = format_dialogflow_response(messages, output_contexts)
    assert response["fulfillmentMessages"] == [
        {"text": {"text": ["Hello!"]}},
        {"text": {"text": ["How can I help you?"]}}
    ]
    assert response["outputContexts"] == output_contexts

def test_format_dialogflow_response_no_contexts():
    # Valid inputs without output contexts
    messages = ["Hello!"]
    response = format_dialogflow_response(messages)
    assert response["fulfillmentMessages"] == [
        {"text": {"text": ["Hello!"]}}
    ]
    assert "outputContexts" not in response

def test_format_dialogflow_response_empty_messages():
    # Edge case: empty messages
    response = format_dialogflow_response([])
    assert response["fulfillmentMessages"] == []
    assert "outputContexts" not in response
#


#---------------------------------------------------------------
#---------------------------------------------------------------
# Test cases for format_rich_response_with_chips

from utils.helper_functions import format_rich_response_with_chips

# Test case 1: Valid inputs with all parameters provided
def test_format_rich_response_with_chips_valid():
    messages = ["Here are your options:", "Let me know what you think!"]
    chips = ["Option 1", "Option 2", "Option 3"]
    output_contexts = [{"name": "test_context", "lifespanCount": 2}]
    
    response = format_rich_response_with_chips(messages, chips, output_contexts)
    
    assert response["fulfillmentMessages"][:2] == [
        {"text": {"text": ["Here are your options:"]}},
        {"text": {"text": ["Let me know what you think!"]}}
    ]
    assert response["fulfillmentMessages"][2]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Option 1"}, {"text": "Option 2"}, {"text": "Option 3"}]
    }
    assert response["outputContexts"] == output_contexts

# Test case 2: Valid inputs without output contexts
def test_format_rich_response_with_chips_no_contexts():
    messages = ["Choose one of the following:"]
    chips = ["Yes", "No"]
    
    response = format_rich_response_with_chips(messages, chips)
    
    assert response["fulfillmentMessages"][0] == {"text": {"text": ["Choose one of the following:"]}}
    assert response["fulfillmentMessages"][1]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Yes"}, {"text": "No"}]
    }
    assert "outputContexts" not in response

# Test case 3: Missing chips (edge case)
def test_format_rich_response_with_chips_missing_chips():
    messages = ["This should still work."]
    chips = []  # No chips provided
    
    response = format_rich_response_with_chips(messages, chips)
    
    assert response["fulfillmentMessages"][0] == {"text": {"text": ["This should still work."]}}
    assert response["fulfillmentMessages"][1]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": []
    }
    assert "outputContexts" not in response

# Test case 4: Empty messages (edge case)
def test_format_rich_response_with_chips_empty_messages():
    messages = []  # No messages
    chips = ["Option A", "Option B"]
    
    response = format_rich_response_with_chips(messages, chips)
    
    assert response["fulfillmentMessages"][0]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Option A"}, {"text": "Option B"}]
    }
    assert "outputContexts" not in response

# Test case 5: Missing both messages and chips (invalid input case)
def test_format_rich_response_with_chips_empty_messages_and_chips():
    messages = []
    chips = []
    
    response = format_rich_response_with_chips(messages, chips)
    
    assert response["fulfillmentMessages"] == [
        {"payload": {"richContent": [[{"type": "chips", "options": []}]]}}
    ]
    assert "outputContexts" not in response

# Test case 6: Valid inputs with complex contexts
def test_format_rich_response_with_chips_complex_contexts():
    messages = ["What do you think?"]
    chips = ["Maybe", "Definitely", "Never"]
    output_contexts = [
        {"name": "context_1", "lifespanCount": 3},
        {"name": "context_2", "lifespanCount": 5}
    ]
    
    response = format_rich_response_with_chips(messages, chips, output_contexts)
    
    assert response["fulfillmentMessages"][0] == {"text": {"text": ["What do you think?"]}}
    assert response["fulfillmentMessages"][1]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Maybe"}, {"text": "Definitely"}, {"text": "Never"}]
    }
    assert response["outputContexts"] == output_contexts


#--------------------------------------------------------

#---------------------------------------------------------------
# Test cases for format_dialogflow_response_with_image_and_chips

from utils.helper_functions import format_dialogflow_response_with_image_and_chips

# Test case 1: Valid inputs with all parameters
def test_format_dialogflow_response_with_image_and_chips_valid():
    messages = ["Here is a product:", "Let me know if you're interested!"]
    image_url = "http://example.com/image.jpg"
    chips = ["Yes", "No", "Maybe"]
    output_contexts = [{"name": "test_context", "lifespanCount": 3}]
    
    response = format_dialogflow_response_with_image_and_chips(messages, image_url, chips, output_contexts)
    
    # Check image
    assert response["fulfillmentMessages"][0]["payload"]["richContent"][0][0] == {
        "type": "image",
        "rawUrl": image_url,
        "accessibilityText": "Product Image"
    }
    # Check text messages
    assert response["fulfillmentMessages"][1]["text"]["text"] == ["Here is a product:"]
    assert response["fulfillmentMessages"][2]["text"]["text"] == ["Let me know if you're interested!"]
    # Check chips
    assert response["fulfillmentMessages"][3]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Yes"}, {"text": "No"}, {"text": "Maybe"}]
    }
    # Check output contexts
    assert response["outputContexts"] == output_contexts

# Test case 2: No image, valid messages and chips
def test_format_dialogflow_response_with_image_and_chips_no_image():
    messages = ["Welcome!", "What do you think?"]
    image_url = None  # No image
    chips = ["Option A", "Option B"]
    
    response = format_dialogflow_response_with_image_and_chips(messages, image_url, chips)
    
    # Check text messages
    assert response["fulfillmentMessages"][0]["text"]["text"] == ["Welcome!"]
    assert response["fulfillmentMessages"][1]["text"]["text"] == ["What do you think?"]
    # Check chips
    assert response["fulfillmentMessages"][2]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Option A"}, {"text": "Option B"}]
    }
    # Ensure no image is present
    assert len(response["fulfillmentMessages"]) == 3
    assert "outputContexts" not in response

# Test case 3: No chips, valid messages and image
def test_format_dialogflow_response_with_image_and_chips_no_chips():
    messages = ["This is the product image."]
    image_url = "http://example.com/product.jpg"
    chips = []  # No chips
    
    response = format_dialogflow_response_with_image_and_chips(messages, image_url, chips)
    
    # Check image
    assert response["fulfillmentMessages"][0]["payload"]["richContent"][0][0] == {
        "type": "image",
        "rawUrl": image_url,
        "accessibilityText": "Product Image"
    }
    # Check text messages
    assert response["fulfillmentMessages"][1]["text"]["text"] == ["This is the product image."]
    # Ensure no chips are present
    assert len(response["fulfillmentMessages"]) == 2
    assert "outputContexts" not in response

# Test case 4: No messages, valid image and chips
def test_format_dialogflow_response_with_image_and_chips_no_messages():
    messages = []  # No messages
    image_url = "http://example.com/another-product.jpg"
    chips = ["Yes", "No"]
    
    response = format_dialogflow_response_with_image_and_chips(messages, image_url, chips)
    
    # Check image
    assert response["fulfillmentMessages"][0]["payload"]["richContent"][0][0] == {
        "type": "image",
        "rawUrl": image_url,
        "accessibilityText": "Product Image"
    }
    # Check chips
    assert response["fulfillmentMessages"][1]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Yes"}, {"text": "No"}]
    }
    # Ensure no messages are present
    assert len(response["fulfillmentMessages"]) == 2
    assert "outputContexts" not in response

# Test case 5: Empty inputs for all parameters
def test_format_dialogflow_response_with_image_and_chips_empty_inputs():
    messages = []
    image_url = None
    chips = []
    
    response = format_dialogflow_response_with_image_and_chips(messages, image_url, chips)
    
    # Ensure response contains no messages
    assert response["fulfillmentMessages"] == []
    assert "outputContexts" not in response

# Test case 6: Valid inputs with complex contexts
def test_format_dialogflow_response_with_image_and_chips_complex_contexts():
    messages = ["Check this out:"]
    image_url = "http://example.com/special.jpg"
    chips = ["Buy Now", "More Info"]
    output_contexts = [
        {"name": "context_1", "lifespanCount": 2},
        {"name": "context_2", "lifespanCount": 4}
    ]
    
    response = format_dialogflow_response_with_image_and_chips(messages, image_url, chips, output_contexts)
    
    # Check image
    assert response["fulfillmentMessages"][0]["payload"]["richContent"][0][0] == {
        "type": "image",
        "rawUrl": image_url,
        "accessibilityText": "Product Image"
    }
    # Check text messages
    assert response["fulfillmentMessages"][1]["text"]["text"] == ["Check this out:"]
    # Check chips
    assert response["fulfillmentMessages"][2]["payload"]["richContent"][0][0] == {
        "type": "chips",
        "options": [{"text": "Buy Now"}, {"text": "More Info"}]
    }
    # Check output contexts
    assert response["outputContexts"] == output_contexts

#---------------------------------------------------------------


from utils.helper_functions import get_system_message

# Test cases for get_system_message

def test_get_system_message_structure():
    # Ensure the function returns a dictionary
    message = get_system_message()
    assert isinstance(message, dict)
    assert "role" in message
    assert "content" in message

def test_get_system_message_content():
    # Verify the actual content matches the expected structure
    message = get_system_message()
    assert message["role"] == "system"
    assert "You are a helpful assistant" in message["content"]
    assert "Supercuts has salons across various regions" in message["content"]
    assert "Provide examples when appropriate" in message["content"]


#---------------------------------------------------------------

import pytest
from utils.helper_functions import extract_session_parameters

# Test cases for extract_session_parameters

def test_extract_session_parameters_valid():
    # Valid case: session-parameters context exists
    output_contexts = [
        {"name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters",
         "parameters": {"person": "John", "email": "john@example.com"}},
        {"name": "projects/test_project/agent/sessions/test_session/contexts/other-context"}
    ]
    result = extract_session_parameters(output_contexts)
    assert result == {"person": "John", "email": "john@example.com"}

def test_extract_session_parameters_missing_context():
    # Case: session-parameters context is missing
    output_contexts = [
        {"name": "projects/test_project/agent/sessions/test_session/contexts/other-context"}
    ]
    result = extract_session_parameters(output_contexts)
    assert result == {}

def test_extract_session_parameters_empty_list():
    # Case: output_contexts is empty
    output_contexts = []
    result = extract_session_parameters(output_contexts)
    assert result == {}

def test_extract_session_parameters_malformed_context():
    # Malformed context (missing 'name' or 'parameters')
    output_contexts = [
        {"name": "projects/test_project/agent/sessions/test_session/contexts/session-parameters"},
        {"parameters": {"person": "John"}}  # Missing 'name'
    ]
    result = extract_session_parameters(output_contexts)
    assert result == {}

def test_extract_session_parameters_invalid_input():
    # Invalid input: not a list
    with pytest.raises(TypeError):
        extract_session_parameters(None)
    with pytest.raises(TypeError):
        extract_session_parameters("invalid")


#------------------------------------------------------------------------------
# Test cases for extract_session 
from utils.helper_functions import extract_session



def test_extract_session_valid():
    # Test valid request body
    body = {
        "session": "projects/test-project/agent/sessions/test-session"
    }
    session = extract_session(body)
    assert session == "projects/test-project/agent/sessions/test-session"

def test_extract_session_missing_body():
    # Test missing body
    with pytest.raises(ValueError, match="Missing request body."):
        extract_session(None)

def test_extract_session_missing_session_key():
    # Test missing 'session' key in the body
    body = {}
    with pytest.raises(ValueError, match="Missing 'session' in request body."):
        extract_session(body)

def test_extract_session_session_not_string():
    # Test 'session' key is not a string
    body = {
        "session": 12345
    }
    with pytest.raises(ValueError, match="'session' must be a string."):
        extract_session(body)

def test_extract_session_invalid_format():
    # Test invalid session format
    body = {
        "session": "invalid_session_format"
    }
    with pytest.raises(ValueError, match="Invalid 'session' format. Must follow 'projects/.../sessions/...'."):
        extract_session(body)

def test_extract_session_empty_session():
    # Test empty string in 'session'
    body = {
        "session": ""
    }
    with pytest.raises(ValueError, match="Invalid 'session' format. Must follow 'projects/.../sessions/...'."):
        extract_session(body)



#------------------------------------------------------------------------------
# Test cases for extract_output_contexts
 

# Import the function to test
from utils.helper_functions import extract_output_contexts
import pytest

def test_extract_output_contexts_valid():
    """Test when 'outputContexts' is present and valid."""
    body = {
        "queryResult": {
            "outputContexts": [
                {"name": "context1", "lifespanCount": 5},
                {"name": "context2", "lifespanCount": 3}
            ]
        }
    }
    result = extract_output_contexts(body)
    assert result == [
        {"name": "context1", "lifespanCount": 5},
        {"name": "context2", "lifespanCount": 3}
    ]

def test_extract_output_contexts_missing_key():
    """Test when 'outputContexts' is missing from queryResult."""
    body = {"queryResult": {}}
    result = extract_output_contexts(body)
    assert result == []  # Should return an empty list

def test_extract_output_contexts_not_a_list():
    """Test when 'outputContexts' is not a list."""
    body = {"queryResult": {"outputContexts": "not_a_list"}}
    with pytest.raises(ValueError, match="'outputContexts' should be a list."):
        extract_output_contexts(body)

def test_extract_output_contexts_empty_body():
    """Test when the body is empty."""
    body = {}
    with pytest.raises(KeyError):
        extract_output_contexts(body)

def test_extract_output_contexts_none_body():
    """Test when the body is None."""
    body = None
    with pytest.raises(TypeError):
        extract_output_contexts(body)


