import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp.server.mcpserver import MCPServer

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_calendar_service():
    creds = None
    token_path = os.path.join(BASE_DIR, 'token.json')
    cred_path = os.path.join(BASE_DIR, 'credentials.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(cred_path):
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        else:
            return None
    return build('calendar', 'v3', credentials=creds)

# 1. Unified Assistant Server
mcp = MCPServer("Personal-Assistant-Server")

# 2. Real Google Calendar Tool
@mcp.tool()
def check_google_calendar(max_events: int = 5) -> str:
    """Fetch real upcoming events from your Google Calendar to find free time."""
    try:
        service = get_calendar_service()
        if not service:
            return "❌ Error: credentials.json file காணப்படவில்லை!"
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_events, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return "📅 Google Calendar Status: அடுத்து வரவிருக்கும் நேரங்களில் எந்த மீட்டிங்கும்/நிகழ்வும் இல்லை! நீங்கள் படம் பார்க்க முழுமையாக ஃப்ரீ (Free)!"
        
        summary_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary_list.append(f"• {event.get('summary', 'Untitled Event')} ({start})")
        
        return "📅 உங்களுடைய Google Calendar Schedule:\n" + "\n".join(summary_list)
    except Exception as e:
        return f"❌ Calendar Error: {str(e)}"

# 3. BookMyShow Tools
@mcp.tool()
def search_theaters(city: str, movie: str) -> str:
    """Search for running movies and theaters in a specific city."""
    return f"'{movie}' படம் {city}-ல் PVR, INOX மற்றும் Sathyam Cinemas-ல் ஓடுகிறது."

@mcp.tool()
def check_shows(theater: str, time_preference: str) -> str:
    """Check show timings based on user's time preference."""
    return f"{theater}-ல் {time_preference} மணிக்கு டிக்கெட்டுகள் Available ஆக உள்ளன."

# 4. Action & Rules Tool
@mcp.tool()
def book_ticket(movie: str, theater: str, otp: str = "") -> str:
    """Book a ticket. Strictly requires a 4-digit OTP."""
    if otp.strip() == "":
        return "❌ Rule Error: பாதுகாப்புக் காரணங்களுக்காக OTP இல்லாமல் டிக்கெட் புக் செய்ய முடியாது!"
    if otp.strip() == "1234":
        return f"✅ Success: {theater}-ல் '{movie}' படத்திற்கு டிக்கெட் வெற்றிகரமாக புக் செய்யப்பட்டது!"
    return "❌ Error: தவறான OTP!"

if __name__ == "__main__":
    mcp.run()