import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Support running tests from repo root or backend/ dir
test_dir = Path(__file__).resolve().parent
backend_dir = test_dir.parent
repo_root = backend_dir.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from calendar_providers.google_calendar import create_event
from calendar_providers.auth import build_credentials_from_token
from utils.datetime_parser import parse_datetime
from utils.logger import log_info, log_error


class TestAuthModule:
    """Tests for calendar/auth.py"""
    
    def test_build_credentials_from_token(self):
        """Test building credentials from token data dict."""
        token_data = {
            "token": "access_token_123",
            "refresh_token": "refresh_token_456",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_123",
            "client_secret": "secret_456",
            "scopes": ["https://www.googleapis.com/auth/calendar.events"]
        }
        
        creds = build_credentials_from_token(token_data)
        
        assert creds.token == "access_token_123"
        assert creds.refresh_token == "refresh_token_456"
        assert creds.client_id == "client_123"


class TestDatetimeParser:
    """Tests for utils/datetime_parser.py"""
    
    def test_parse_datetime_iso_format(self):
        """Test parsing ISO 8601 datetime string."""
        dt_str = "2026-02-20T14:30:00"
        result = parse_datetime(dt_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 20
        assert result.hour == 14
        assert result.minute == 30
    
    def test_parse_datetime_with_timezone(self):
        """Test parsing ISO datetime with timezone."""
        dt_str = "2026-02-20T14:30:00+00:00"
        result = parse_datetime(dt_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2026
    
    def test_parse_datetime_invalid_format(self):
        """Test parsing invalid datetime raises error."""
        with pytest.raises(ValueError, match="Invalid datetime format"):
            parse_datetime("invalid-date")


class TestCalendarModule:
    """Tests for calendar/google_calendar.py"""
    
    @patch('backend.calendar_providers.google_calendar.build')
    def test_create_event_success(self, mock_build):
        """Test successful event creation."""
        # Mock the Google Calendar API
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        mock_events = MagicMock()
        mock_service.events.return_value = mock_events
        mock_insert = MagicMock()
        mock_events.insert.return_value = mock_insert
        
        mock_execute = MagicMock(return_value={
            'id': 'event_123',
            'htmlLink': 'https://calendar.google.com/calendar/u/0/r/eventedit/event_123'
        })
        mock_insert.execute.return_value = mock_execute.return_value
        
        token_data = {
            "token": "access_token",
            "refresh_token": "refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar.events"]
        }
        
        result = create_event(
            name="John Doe",
            datetime_str="2026-02-20T14:30:00",
            title="Team Meeting",
            token_data=token_data
        )
        
        assert result['id'] == 'event_123'
        assert 'htmlLink' in result
        assert 'message' in result
        assert "Team Meeting" in result['message']
    
    @patch('backend.calendar_providers.google_calendar.build')
    def test_create_event_uses_correct_calendar_id(self, mock_build):
        """Test that create_event uses correct calendar ID."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        mock_events = MagicMock()
        mock_service.events.return_value = mock_events
        mock_insert = MagicMock()
        mock_events.insert.return_value = mock_insert
        mock_insert.execute.return_value = {
            'id': 'event_123',
            'htmlLink': 'https://calendar.google.com/calendar/u/0/r/eventedit/event_123'
        }
        
        token_data = {
            "token": "access_token",
            "refresh_token": "refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar.events"]
        }
        
        create_event(
            name="Jane",
            datetime_str="2026-03-15T10:00:00",
            title="1:1 Meeting",
            token_data=token_data
        )
        
        # Verify insert was called with 'primary' calendar ID
        mock_events.insert.assert_called_once()
        call_kwargs = mock_events.insert.call_args[1]
        assert call_kwargs['calendarId'] == 'primary'
    
    @patch('backend.calendar_providers.google_calendar.build')
    def test_create_event_sets_correct_duration(self, mock_build):
        """Test that events are created with 1-hour duration."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        mock_events = MagicMock()
        mock_service.events.return_value = mock_events
        mock_insert = MagicMock()
        mock_events.insert.return_value = mock_insert
        mock_insert.execute.return_value = {
            'id': 'event_123',
            'htmlLink': 'https://calendar.google.com/calendar/u/0/r/eventedit/event_123'
        }
        
        token_data = {
            "token": "access_token",
            "refresh_token": "refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar.events"]
        }
        
        create_event(
            name="Bob",
            datetime_str="2026-02-25T09:00:00",
            title="Standup",
            token_data=token_data
        )
        
        # Extract the event body from the insert call
        call_kwargs = mock_events.insert.call_args[1]
        event_body = call_kwargs['body']
        
        start_time = datetime.fromisoformat(event_body['start']['dateTime'])
        end_time = datetime.fromisoformat(event_body['end']['dateTime'])
        duration = end_time - start_time
        
        # Should be 1 hour
        assert duration.total_seconds() == 3600
    
    @patch('backend.calendar_providers.google_calendar.build')
    def test_create_event_failure_handling(self, mock_build):
        """Test error handling when event creation fails."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events.side_effect = Exception("API Error")
        
        token_data = {
            "token": "access_token",
            "refresh_token": "refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar.events"]
        }
        
        with pytest.raises(Exception, match="API Error"):
            create_event(
                name="Alice",
                datetime_str="2026-02-20T14:30:00",
                title="Meeting",
                token_data=token_data
            )


class TestLoggerModule:
    """Tests for utils/logger.py"""
    
    @patch('backend.utils.logger.logging.info')
    def test_log_info(self, mock_log):
        """Test log_info function."""
        log_info("Test info message")
        mock_log.assert_called_once_with("Test info message")
    
    @patch('backend.utils.logger.logging.error')
    def test_log_error(self, mock_log):
        """Test log_error function."""
        log_error("Test error message")
        mock_log.assert_called_once_with("Test error message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

