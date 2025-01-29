from unittest.mock import patch, MagicMock
import pytest



#--------------------------------------------------------------------
# Test cases for create_event
from utils.calendar_services import create_event


@patch("utils.calendar_services.calendar.events")
@patch("utils.calendar_services.CALENDAR_ID", "primary")  # Mock CALENDAR_ID
def test_create_event_success(mock_events):
    # Mock the insert() call
    mock_insert = mock_events.return_value.insert
    mock_execute = mock_insert.return_value.execute
    mock_execute.return_value = {"id": "test_event_id", "summary": "Test Event"}

    # Valid inputs
    summary = "Test Event"
    description = "This is a test event."
    start_time = "2025-01-27T02:00:00+01:00"
    time_zone = "Europe/Belgrade"

    # Call the function
    result = create_event(summary, description, start_time, time_zone)

    # Assert the response
    assert result == {"id": "test_event_id", "summary": "Test Event"}
    mock_events.assert_called_once()
    mock_insert.assert_called_once_with(
        calendarId="primary",  # Ensure consistency
        body={
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": "2025-01-27T02:00:00+01:00",
                "timeZone": time_zone,
            },
            "end": {
                "dateTime": "2025-01-27T02:30:00+01:00",
                "timeZone": time_zone,
            },
        },
    )



#--------------------------------------------------------------------
# Test cases for build_slot_check_contexts
from utils.calendar_services import build_slot_check_contexts



def test_build_slot_check_contexts_valid():
    session = "projects/test-project/agent/sessions/test-session-id"
    next_context = "await-slot-confirmation"
    session_parameters = {"key": "value"}
    lifespan = 2

    result = build_slot_check_contexts(session, next_context, session_parameters, lifespan)

    expected = [
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

    assert result == expected

def test_build_slot_check_contexts_invalid_session():
    with pytest.raises(ValueError, match="Session must be a string."):
        build_slot_check_contexts(123, "await-slot-confirmation", {"key": "value"})

def test_build_slot_check_contexts_invalid_next_context():
    with pytest.raises(ValueError, match="Next context must be a string."):
        build_slot_check_contexts("projects/test/agent/sessions/test", 123, {"key": "value"})

def test_build_slot_check_contexts_invalid_session_parameters():
    with pytest.raises(ValueError, match="Session parameters must be a dictionary."):
        build_slot_check_contexts("projects/test/agent/sessions/test", "await-slot-confirmation", ["not", "a", "dict"])

def test_build_slot_check_contexts_custom_lifespan():
    session = "projects/test-project/agent/sessions/test-session-id"
    next_context = "await-slot-confirmation"
    session_parameters = {"key": "value"}
    lifespan = 10

    result = build_slot_check_contexts(session, next_context, session_parameters, lifespan)

    assert result[0]['lifespanCount'] == lifespan
    assert result[1]['lifespanCount'] == lifespan

def test_build_slot_check_contexts_empty_parameters():
    session = "projects/test-project/agent/sessions/test-session-id"
    next_context = "await-slot-confirmation"
    session_parameters = {}

    result = build_slot_check_contexts(session, next_context, session_parameters)

    assert result[1]['parameters'] == session_parameters






#--------------------------------------------------------------------
# Test cases for build_slot_check_contexts
from utils.calendar_services import get_free_busy



import pytest
from unittest.mock import patch

@pytest.mark.usefixtures("monkeypatch")  # Enable monkeypatch fixture
@patch("utils.calendar_services.calendar.freebusy")
def test_get_free_busy_valid_inputs(mock_freebusy, monkeypatch):
    # Monkeypatch the CALENDAR_ID
    monkeypatch.setattr("utils.calendar_services.CALENDAR_ID", "test_calendar_id")

    # Mock API response
    mock_execute = mock_freebusy.return_value.query.return_value.execute
    mock_execute.return_value = {
        "calendars": {
            "test_calendar_id": {  # Match the mocked CALENDAR_ID
                "busy": [
                    {"start": "2025-01-27T02:00:00+01:00", "end": "2025-01-27T02:30:00+01:00"}
                ]
            }
        }
    }

    # Valid inputs
    start_time = "2025-01-27T02:00:00+01:00"
    end_time = "2025-01-27T03:00:00+01:00"
    timezone = "Europe/Belgrade"

    result = get_free_busy(start_time, end_time, timezone)

    # Assert the response
    assert result == [{"start": "2025-01-27T02:00:00+01:00", "end": "2025-01-27T02:30:00+01:00"}]
    mock_freebusy.return_value.query.assert_called_once()



@patch("utils.calendar_services.calendar.freebusy")
def test_get_free_busy_invalid_time_format(mock_freebusy):
    # Invalid start_time
    start_time = "invalid-time"
    end_time = "2025-01-27T03:00:00+01:00"
    timezone = "Europe/Belgrade"

    result = get_free_busy(start_time, end_time, timezone)

    # Assert empty list returned
    assert result == []
    mock_freebusy.return_value.query.assert_not_called()

@patch("utils.calendar_services.calendar.freebusy")
def test_get_free_busy_api_error(mock_freebusy):
    # Mock API to raise an exception
    mock_execute = mock_freebusy.return_value.query.return_value.execute
    mock_execute.side_effect = Exception("API Error")

    start_time = "2025-01-27T02:00:00+01:00"
    end_time = "2025-01-27T03:00:00+01:00"
    timezone = "Europe/Belgrade"

    result = get_free_busy(start_time, end_time, timezone)

    # Assert empty list returned
    assert result == []
    mock_freebusy.return_value.query.assert_called_once()









#--------------------------------------------------------------------
# Test cases for extract_and_validate_date_time
from utils.calendar_services import extract_and_validate_date_time



def test_extract_and_validate_date_time_valid_single():
    body = {
        "queryResult": {
            "parameters": {
                "date-time": [{"date_time": "2025-01-27T02:00:00+01:00"}]
            }
        }
    }
    is_valid, date_time = extract_and_validate_date_time(body, "await-date-time", {})
    assert is_valid is True
    assert date_time == "2025-01-27T02:00:00+01:00"

def test_extract_and_validate_date_time_valid_list():
    body = {
        "queryResult": {
            "parameters": {
                "date-time": [
                    {"date_time": "2025-01-27T02:00:00+01:00"},
                    {"date_time": "2025-01-28T02:00:00+01:00"}
                ]
            }
        }
    }
    is_valid, date_time = extract_and_validate_date_time(body, "await-date-time", {})
    assert is_valid is True
    assert date_time == "2025-01-27T02:00:00+01:00"

def test_extract_and_validate_date_time_missing():
    body = {
        "queryResult": {
            "parameters": {}
        }
    }
    is_valid, date_time = extract_and_validate_date_time(body, "await-date-time", {})
    assert is_valid is False
    assert date_time == ""

def test_extract_and_validate_date_time_empty():
    body = {
        "queryResult": {
            "parameters": {
                "date-time": []
            }
        }
    }
    is_valid, date_time = extract_and_validate_date_time(body, "await-date-time", {})
    assert is_valid is False
    assert date_time == ""

def test_extract_and_validate_date_time_invalid_format():
    body = {
        "queryResult": {
            "parameters": {
                "date-time": [{"invalid_key": "value"}]
            }
        }
    }
    is_valid, date_time = extract_and_validate_date_time(body, "await-date-time", {})
    assert is_valid is False
    assert date_time == ""

def test_extract_and_validate_date_time_non_dict_list():
    body = {
        "queryResult": {
            "parameters": {
                "date-time": ["2025-01-27T02:00:00+01:00", "invalid"]
            }
        }
    }
    is_valid, date_time = extract_and_validate_date_time(body, "await-date-time", {})
    assert is_valid is True
    assert date_time == "2025-01-27T02:00:00+01:00"




#--------------------------------------------------------------------
# Test cases for convert_to_utc_and_store 
from utils.calendar_services import convert_to_utc_and_store

import pytest


def test_convert_to_utc_and_store_valid():
    session_parameters = {}
    date_time = "2025-01-27T02:00:00+01:00"  # Europe/Belgrade (UTC+1)
    timezone = "Europe/Belgrade"
    
    result = convert_to_utc_and_store(date_time, session_parameters, timezone)
    
    assert result["date_time"] == date_time
    assert result["utc_time"] == "2025-01-27T01:00:00+00:00"  # Converted to UTC
    assert result["timezone"] == timezone

def test_convert_to_utc_and_store_invalid_date_time():
    session_parameters = {}
    invalid_date_time = "invalid-date-time"
    
    with pytest.raises(ValueError, match="Invalid date-time format"):
        convert_to_utc_and_store(invalid_date_time, session_parameters, "UTC")

def test_convert_to_utc_and_store_default_timezone():
    session_parameters = {}
    date_time = "2025-01-27T02:00:00+00:00"  # UTC
    
    result = convert_to_utc_and_store(date_time, session_parameters)
    
    assert result["date_time"] == date_time
    assert result["utc_time"] == date_time  # No conversion needed
    assert result["timezone"] == "UTC"

def test_convert_to_utc_and_store_empty_session_parameters():
    session_parameters = {}  # Empty session parameters
    date_time = "2025-01-27T02:00:00+01:00"  # Europe/Belgrade (UTC+1)
    timezone = "Europe/Belgrade"
    
    result = convert_to_utc_and_store(date_time, session_parameters, timezone)
    
    assert result["date_time"] == date_time
    assert result["utc_time"] == "2025-01-27T01:00:00+00:00"
    assert result["timezone"] == timezone

def test_convert_to_utc_and_store_different_timezone():
    session_parameters = {}
    date_time = "2025-01-27T02:00:00-05:00"  # UTC-5
    timezone = "America/New_York"
    
    result = convert_to_utc_and_store(date_time, session_parameters, timezone)
    
    assert result["date_time"] == date_time
    assert result["utc_time"] == "2025-01-27T07:00:00+00:00"  # Converted to UTC
    assert result["timezone"] == timezone




#-----------------------------------------------------------------------------------------------------------
# Test cases for find_available_slot 
from utils.calendar_services import find_available_slot

from unittest.mock import patch
import pytest
from datetime import datetime, timedelta



@patch("utils.calendar_services.get_free_busy")
def test_find_available_slot_free_first_attempt(mock_get_free_busy):
    # Mock `get_free_busy` to return no busy slots
    mock_get_free_busy.return_value = []

    # Inputs
    start_time = "2025-01-27T02:00:00+01:00"
    timezone = "Europe/Belgrade"

    # Call the function
    result, slot = find_available_slot(start_time, timezone)

    # Assertions
    assert result is True
    assert slot["is_original"] is True
    assert slot["local_time"].isoformat() == datetime.fromisoformat(start_time).isoformat()

@patch("utils.calendar_services.get_free_busy")
def test_find_available_slot_no_free_slots(mock_get_free_busy):
    # Mock `get_free_busy` to always return busy slots
    mock_get_free_busy.return_value = [{"start": "2025-01-27T02:00:00+01:00", "end": "2025-01-27T02:30:00+01:00"}]

    # Inputs
    start_time = "2025-01-27T02:00:00+01:00"
    timezone = "Europe/Belgrade"

    # Call the function
    result, slot = find_available_slot(start_time, timezone)

    # Assertions
    assert result is False
    assert slot == {}

@patch("utils.calendar_services.get_free_busy")
def test_find_available_slot_free_after_attempts(mock_get_free_busy):
    # Mock `get_free_busy` to return busy for the first two attempts, then free
    mock_get_free_busy.side_effect = [
        [{"start": "2025-01-27T02:00:00+01:00", "end": "2025-01-27T02:30:00+01:00"}],  # Busy first attempt
        [{"start": "2025-01-27T02:30:00+01:00", "end": "2025-01-27T03:00:00+01:00"}],  # Busy second attempt
        []  # Free on third attempt
    ]

    # Inputs
    start_time = "2025-01-27T02:00:00+01:00"
    timezone = "Europe/Belgrade"

    # Call the function
    result, slot = find_available_slot(start_time, timezone)

    # Assertions
    assert result is True
    assert slot["is_original"] is False
    assert slot["local_time"].isoformat() == (datetime.fromisoformat(start_time) + timedelta(minutes=60)).isoformat()

@patch("utils.calendar_services.get_free_busy")
def test_find_available_slot_custom_max_attempts(mock_get_free_busy):
    # Mock `get_free_busy` to always return busy slots
    mock_get_free_busy.return_value = [{"start": "2025-01-27T02:00:00+01:00", "end": "2025-01-27T02:30:00+01:00"}]

    # Inputs
    start_time = "2025-01-27T02:00:00+01:00"
    timezone = "Europe/Belgrade"
    max_attempts = 2

    # Call the function
    result, slot = find_available_slot(start_time, timezone, max_attempts=max_attempts)

    # Assertions
    assert result is False
    assert slot == {}









