# calendar/google_calendar.py
from googleapiclient.discovery import build
from datetime import timedelta
from utils.datetime_parser import parse_datetime
from utils.logger import log_info, log_error
from calendar_providers.auth import build_credentials_from_token, get_service_account_credentials
import os

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
# Add your email here to receive calendar invites
DEFAULT_ATTENDEE_EMAIL = os.getenv("DEFAULT_ATTENDEE_EMAIL", "")

def create_event(name: str, datetime_str: str, title: str, token_data: dict = None, duration_minutes: int = 60, timezone: str = "America/New_York", attendee_email: str = None) -> dict:
    """
    Create a Google Calendar event.
    
    Args:
        name: Person's name (for description)
        datetime_str: ISO 8601 datetime string
        title: Event title
        token_data: Token dict with auth credentials (optional, uses service account if not provided)
        duration_minutes: Event duration in minutes (default 60)
        timezone: Event timezone
        attendee_email: Email to invite as attendee (optional)
    """
    try:
        log_info(f'🎯 Initializing Google Calendar creation for {title}')
        
        # Try to use service account first, fall back to token_data
        if token_data:
            log_info('Building credentials from token data...')
            creds = build_credentials_from_token(token_data)
        else:
            log_info('Building credentials from service account...')
            creds = get_service_account_credentials()
        
        log_info('Building Google Calendar service...')
        service = build('calendar', 'v3', credentials=creds)

        log_info(f'Parsing datetime: {datetime_str}')
        start = parse_datetime(datetime_str)
        end = start + timedelta(minutes=duration_minutes)

        # Google Calendar accepts local datetime + separate timeZone.
        # Avoid embedding UTC offsets here, which can shift local meeting times.
        start_local = start.replace(tzinfo=None)
        end_local = end.replace(tzinfo=None)
        
        log_info(f'Event time: {start_local} to {end_local} ({timezone})')

        event = {
            "summary": title,
            "description": f"Meeting with {name}",
            "start": {"dateTime": start_local.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end_local.isoformat(), "timeZone": timezone}
        }
        
        # Add attendee if email is provided (so user receives calendar invite)
        email_to_invite = attendee_email or DEFAULT_ATTENDEE_EMAIL
        if email_to_invite:
            event["attendees"] = [{"email": email_to_invite}]
            log_info(f'Adding attendee: {email_to_invite}')
        
        log_info(f'Event object created: {event}')
        log_info('Inserting event into Google Calendar...')

        # Use sendUpdates to send email invites to attendees
        created = service.events().insert(
            calendarId=CALENDAR_ID, 
            body=event,
            sendUpdates='all' if email_to_invite else 'none'
        ).execute()
        log_info(f"✅ Event created: {created.get('id')} for {name}")
        log_info(f"Event details: summary={created.get('summary')}, start={created.get('start')}")
        
        return {
            "id": created.get('id'),
            "htmlLink": created.get('htmlLink'),
            "message": f"Meeting '{title}' scheduled for {start_local.strftime('%A, %B %d at %H:%M')}."
        }
    
    except Exception as e:
        log_error(f"❌ Failed to create event: {str(e)}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        raise
