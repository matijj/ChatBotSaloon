from unittest.mock import patch
from utils.google_sheets import write_data

def test_write_data_success():
    with patch("utils.google_sheets.sheet.values") as mock_values:
        # Mock the API response
        mock_values.return_value.append.return_value.execute.return_value = {"updates": {"updatedRows": 1}}

        # Call the function
        result = write_data("list!A1", [["John Doe", "john@example.com", "2025-01-05 14:00:00"]])

        # Assertions
        mock_values.return_value.append.assert_called_once_with(
            spreadsheetId="1jw6PUUds9VbdOIyBlNvmehHQFdfNuWteYJBRZwUInQA",
            range="list!A1",
            valueInputOption="RAW",
            body={"values": [["John Doe", "john@example.com", "2025-01-05 14:00:00"]]}
        )
        assert result == {"updates": {"updatedRows": 1}}






def test_write_data_failure():
    with patch("utils.google_sheets.sheet.values") as mock_values:
        # Simulate API error
        mock_values.return_value.append.return_value.execute.side_effect = Exception("API Error")

        # Call the function
        result = write_data("list!A1", [["John Doe", "john@example.com", "2025-01-05 14:00:00"]])

        # Assertions
        mock_values.return_value.append.assert_called_once()
        assert result is None  # Ensure the function returns None on failure





#def test_write_data_invalid_data():
#    with patch("utils.google_sheets.sheet.values") as mock_values:
#        # Mock API response
#        mock_values.return_value.append.return_value.execute.return_value = {"updates": {"updatedRows": 0}}
#
#        # Call the function with empty data
#        result = write_data("list!A1", [])
#
#        # Assertions
#        mock_values.return_value.append.assert_not_called()  # Ensure no API call is made
#        assert result == {"updates": {"updatedRows": 0}}
#


def test_write_data_invalid_data():
    with patch("utils.google_sheets.sheet.values") as mock_values:
        # Call the function with empty data
        result = write_data("list!A1", [])

        # Assertions
        mock_values.return_value.append.assert_not_called()  # Ensure no API call is made
        assert result is None  # Expect None when no data is provided








